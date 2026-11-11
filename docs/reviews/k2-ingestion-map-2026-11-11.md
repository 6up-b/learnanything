# Ingestion and synthesis map (K2, 2026-11-11)

Refactor arc K, step K2, job 1: the deep map of ingestion and synthesis that the Nov 8 map (`docs/reviews/architecture-map-2026-11-08.md`) read by outline only. It names problems and recommends nothing; job 2 (the structure strategy) stands on it after a Codex adversarial check. **Base: main `565aee8724`** (arc C closed, K1 landed), branch `refactor/k2-ingestion-map`. Docs only; no source, test or vault note changed.

## Summary for the owner

Ingestion and synthesis is 117 modules and about 50,000 code lines: pipeline, synthesis, authoring's ingest paths, proposals, facet identity, `ingest`, sources and the sidecar's ingest handlers. It works, and several of its parts are good (the ingest drain's fencing, per-window and per-shard checkpoints, a pure mint gate, the gates). What's expensive is that the same idea is built several times, and that the inputs synthesis reads are chosen silently.

**The five most costly findings:**

1. **Keep-ahead appends re-send the whole book, with no checkpoint and no ceiling (§7 KX1, KX2).** The planner queues each chapter's build with no new-unit list, so every append sends every inventory of every chapter built so far, and only the neighbourhood is capped. The call has no checkpoint, no generation limit and no input ceiling, so a retry re-pays it and an over-budget answer fails the same way every time. The cost is quadratic in chapters: projected from the copies' inventory sizes, roughly 10^7-10^8 input tokens over a whole textbook against 10^6-10^7, and the last appends would exceed any route's context. It hasn't cost you yet: keep-ahead never ran on the copied vaults.
2. **Apply recovery can overwrite newer YAML, and only `doctor --fix-state` runs it (§2.8 KD2).** Each apply intent records a pre-image hash that nothing reads. A crash between two file renames leaves a half-applied vault that the app serves and the next accept builds on. The module says startup recovers it; nothing does.
3. **The decisions that set what synthesis reads are silent, and the boundary loses identity (§3.1 KB1, §4 KO1, §7 KX3).** Synthesis picks a unit's *oldest* inventory by revision and unit id alone, so a new prompt, a new model or a re-read whose text changed is paid for and then ignored. The manifest records only version labels. Which units an append sent and why a chapter was withheld aren't stored either. A wrong study map can't be traced to its inputs from rows.
4. **Two synthesis orchestrators and a 1,081-line normalizer (§1 KP1, KP5; §6 KH1).** Bootstrap and append are the same 250-310-line shape written twice. Since Oct 1, 12 of the 15 commits that changed the append also changed the bootstrap, and the append's comments record three invariants it once missed. Both feed `_normalize`, twelve stages in one frame with shared mutable state, where facet identity, the mint gate and aliasing meet.
5. **Six lease stores, five heartbeat loops and six checkpoint recipes (§3.3 KB2, §3.4 KB3).** The coverage audit's "four reimplementations" undercounts. Two heartbeats are verbatim copies, two lease users commit after their lease lapses, and one mixes clocks. The checkpoint keys disagree on rendered prompt versus label and on whether the output budget belongs in the key. Four paid calls on the synthesis path have no checkpoint at all: append, concept-graph structuring, persona fire calls and epigraphs.

**Also worth your attention:**
- **Every append's concepts, facets and LOs wait for review (KX4).** Only provenance links auto-apply. "Chapter 3" is incidental: it depends on how many chapters the first build took. Changing that is your call (spec §10.2-10.3).
- **The manifest hash does three jobs (KX5).** It over-invalidates (every practice item, the algorithm version, budgets, config dumps) and under-invalidates (append's revision diff, inventory content). An append cache hit never applies.
- **A durable arXiv import reads only the abstract page (KD3).** A test-only module next to it fetches the full text, under the live fetch's function name.
- **The desktop re-implements at least eight backend rules, and three disagree (KB4):** assessment roles, retry eligibility and the image kind.
- **The journey you use most, Add → automatic build → keep-ahead, has no vault note.** Neither do facet identity and write-ahead apply (KV1).

**Change cost (§6), files touched (src / tests / frontend):**

| change | files | plumbing |
|---|---|---|
| a source type (audio) | 11 / 10 / 0 | 0 |
| an extractor (GLM-OCR with images, net) | 18 / 7 / 10 | 743 generated notes |
| a synthesis pass (epigraphs) | 9 / 8 / 0, both orchestrators | 0 |
| a facet rule (exam authority at the meaning write) | 8 / 7 / 0, both orchestrators | 0 |

**Counts:**
- Six lease stores and five heartbeat loops.
- Six checkpoint recipes, three run-level reuse keys, and four paid calls with neither.
- One ADR-017 decision record in the whole area.
- The Sep 6 ingestion review: of its ten findings, eight are fixed or resolved by deletion. Two are open, both in append: cached apply (finding 7) and output limits (finding 4).

**Limits.** Code-traced, not run. No synthesis receipt exists in the copies, so append spend is measured once (July) and keep-ahead's is projected. The delegated sweeps were spot-checked, and what wasn't is listed under "Not verified".

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
| **total** | | **117** | **70,297** | **49,710** | **2,385** | **11** |

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
| KP2 | high | **`jobs.py` is a registry of 21 job types and the durable host in one 5,852-line module.** It holds ingest handlers beside unrelated ones (`figure_rich`, `concept_animation`, `rung_variant`, `goal_population`, `question_promotion`, AD commissions), `DurableIngestJobs` (about 64 methods, `content/pipeline/jobs.py:4030`), the reading sweep (`:3971`), GLM-OCR checkpoints (`:352`) and the native media route (`:676`). `RunnerServices` carries 22 per-type client factories (`content/pipeline/runner.py:193`). Every new job type edits this module, `runner.py` and usually `APPLYING_JOB_TYPES` (`content/pipeline/jobs.py:3941`). | `content/pipeline/jobs.py:3910-3932`, `:3941-3961` |
| KP3 | medium | **`add_source.py` (70 public names) is the whole automatic-build product in one module:** Add, chapter order, consent and money, automatic subjects, the job ledger, Undo, the planner job, keep-ahead follow-ups and the book's status line (section headers at `:128`, `:341`, `:481`, `:1098`, `:1135`, `:1245`, `:1339`, `:1713`, `:2143`). It's readable by section, but it's the one place every automatic-build change lands, and it and `jobs.py` import each other. | `content/pipeline/add_source.py` |
| KP4 | medium | **The area's layers import each other both ways** (four subpackage pairs, five module cycles), and 43% of its imports hide in functions. "Can identity change without synthesis?" can't be answered from the imports. | §1.2 |
| KP5 | medium | **The two synthesis orchestrators are the same 250-310-line shape written twice** (`_create_study_map`, `_append`): inputs, manifest, cache, agent run, model call, facet identity, normalize, gates, persist, apply, epigraphs. §6 shows each cross-cutting change edits both, and §2.5 shows the append copy repeatedly missing the create copy's invariants. | `content/synthesis/source_set_synthesis.py:2109`, `content/synthesis/source_append.py:224` |
| KP6 | low | **`KNOWN_JOB_TYPES` is a stale vocabulary:** 11 of the 21 handled job types (`auto_study_map`, `reader_quick_check`, `practice_expansion`, ...) aren't in it, and only one test reads it. | `content/pipeline/runner.py:109`; `tests/test_coverage_on_extract.py:107` |
| KP7 | low | Shallow modules are few (12 of 117) and cheap: `ingest/detect.py` (13 lines), `content/sources/front_matter.py`, `content/synthesis/coverage_rollup.py`, a handful of one-importer helpers. Not a cost. | Appendix A |

## 2. The journeys end to end

Every durable "add" ends in one job, `handle_import` (`content/pipeline/jobs.py:2066`); the journeys differ in how they get there and in what they extract. After extraction, model work follows in its own jobs: the automatic-build planner, inventory, then bootstrap or append synthesis. All of them run on the job host (§3.3), under the desktop sidecar or a CLI drain; the phone host refuses to bind ingest (`learnloop_sidecar/context.py:322-326`).

**Persistence legend.** SQLite tables unless marked: **[Y]** a vault YAML file, **[B]** a blob under `canonical-sources/raw/`.

### 2.1 Add a source: the shared spine

1. **Entry.**
   - Add (the default journey): sidecar `add_source` (`learnloop_sidecar/handlers/first_run.py:93-111`) → `add_source()` (`content/pipeline/add_source.py:189`). It classifies with `resolve_source` (`content/pipeline/add_source.py:216`; `ingest/resolution.py:33-75`) and returns `existing` for a book already in the library with text or an Add in flight (`content/pipeline/add_source.py:220-231`). A local file is registered at once (`:236-252`); a link is only queued. Then `enqueue_add_source` (`content/pipeline/jobs.py:4182`) enqueues one batch, `[import{require_upload_ok}, auto_study_map]` (`:4206-4231`).
   - The Ingest screen's import: `start_import_batch` (`learnloop_sidecar/handlers/ingest.py:265`) → `enqueue_import` (`content/pipeline/jobs.py:4725`), with an explicit engine in `pdf_config` (`:4757-4759`).
   - The legacy lane: `start_ingest` (`learnloop_sidecar/handlers/ingest.py:209`) → `DurableIngestJobs.start` (`content/pipeline/jobs.py:4612`), batch `[import, legacy_ingest | exam_ingest]` (`:4625-4651`); the CLI's `learnloop ingest` runs `ingest_canonical_source` in one shot (`cli/runtime.py:417`).
2. **Classify** (`content/pipeline/jobs.py:2089-2094`): an existing book keeps its kind and URI; otherwise `resolve_source`.
3. **Fetch** (`:2099-2118`): an existing book reads its own original bytes (`content/pipeline/reread.py:89`, verified against `asset_hash`); otherwise `default_fetch` (`:96`): a local file directly, a URL through `source_ingestion.fetch_source(kind="youtube_video" | "website_page", raw_only=True)` (`:110-118`), with a disk cache at `.learnloop/source-cache/` and an offline fallback (`content/pipeline/source_ingestion.py:1169-1206`). Fetch time and the server's bytes enter identity for web, arXiv and YouTube.
4. **Register** `register_source_revision` (`content/sources/source_library.py:33`): `asset_hash` = SHA-256 of the raw bytes (`ingest/hashing.py:51`); **[B]** the blob at `canonical-sources/raw/sha256-<hex>`, written atomically (`ingest/originals.py:23-53`); `source_artifacts` by (kind, canonical URI), a new `src_<ulid>` (`content/sources/source_library.py:80-97`); `source_revisions` reused for the same (source, asset hash), else a new `rev_<ulid>` superseding the last (`:101-124`). A new revision becomes current only before the book has a completed reading (`:128-129`).
5. **Extraction identity and cache.** `default_extraction_identity` (`content/pipeline/jobs.py:558`) gives extractor, version, model versions and config; `extraction_request_hash` (`ingest/hashing.py:61-86`) hashes them with the revision id, the page selection and `IR_SCHEMA_VERSION` (`ingest/ir.py:23`), API keys stripped. A hit on `extraction_run_by_request_hash` (`content/pipeline/jobs.py:2157`) reuses the run. Because `revision_id` (a ULID) is inside it, the hash is per vault, not content-addressed.
6. **Extract** on a miss: `default_extract` (`:468`) by kind (below); the request hash is recomputed from what actually ran, and a stand-in extractor adds `fallback_from` (`:2169-2185`, `:2262`).
7. **Persist** `source_extraction_runs` (`ext_<ulid>`, `:2194`; `db/repositories.py:20039`), then `persist_document_ir` (`db/repositories.py:20127`) replaces `source_document_units` (with each unit's `semantic_hash`), `source_document_blocks` (with `content_hash`) and `source_document_assets`, and `complete_extraction_run` stores `extraction_result_hash` (`ingest/hashing.py:94-102`). Span ids are ordinal, `s{n}` (`ingest/extractors/normalizers.py:67`), so they are stable only within one extraction.
8. **Adopt and carry over** (`content/pipeline/jobs.py:2228-2236`): `adopt_revision` (`content/pipeline/reread.py:146`) and `carry_over` (`:396`, §2.3).
9. **Follow-on jobs** owed by a completed extraction: the source-vector backfill (`queue_source_vectors`, `content/pipeline/jobs.py:2282`), and, each behind its switch, the local index, the fallback space and curriculum coverage (§3.1).
10. **Plan the first build** (`run_auto_study_map`, `content/pipeline/add_source.py:1524`, §2.5).

No vault YAML is written on this path, and no model is called except for GLM-OCR, audio transcription and native media. Every job's model calls are recorded in `model_call_receipts` under `owner_kind=ingest_job` (`content/pipeline/runner.py:1031`).

### 2.2 By source type

| type | classify | extract | model call | what `asset_hash` covers |
|---|---|---|---|---|
| **PDF** | `pdf` (`ingest/resolution.py:48`, `:60`) | `_document_extractor` (`content/pipeline/jobs.py:260`) → `pdf_extractor_for` (`ingest/extractors/__init__.py:84`): GLM-OCR when a z.ai key or a reachable local server is set (`ingest/extractors/glm_ocr.py:185-210`), else Datalab if chosen, else local Marker in a worker process (`ingest/extractors/marker.py:384-407`), else pypdf (`ingest/extractors/__init__.py:132-155`). `extract_with_fallback` (`:165`) falls GLM → local, Marker → pypdf, and writes the fallback into `health_json` flags (`:196-211`). Hosted GLM under `auto` without the upload OK falls back locally, or, on an Add, raises the OK card (`content/pipeline/jobs.py:298-312`) | GLM-OCR `document_layout_recognition` (`ingest/extractors/glm_ocr.py:461`), windows of up to 30 pages (`MAX_PAGES_PER_REQUEST`, `:99`, `:326`), each answer checkpointed (`glm_ocr_window`, key at `:416-420`) | the file |
| **arXiv** | any arxiv.org host, or a bare id → `/abs/<id>` (`ingest/resolution.py:44-54`) | **the durable import fetches the `/abs/` landing page as a web page** (`content/pipeline/jobs.py:110`) and extracts it with trafilatura (`:535-540`); only an `/pdf/` URL takes the PDF path (`:243-246`). The legacy lane fetches `/html/` (`content/pipeline/source_ingestion.py:700-706`) but then swaps in the import's IR (`:247-248`) | none | the landing page's HTML |
| **YouTube** | `youtube` | captions through youtube-transcript-api, manual English else automatic (`content/pipeline/source_ingestion.py:1209`; `allow_auto_captions=True`, `content/pipeline/jobs.py:115`); oEmbed title (`:130-147`); `captions_to_ir` (`:528-531`) | none | the captions JSON, so changed automatic captions mint a new revision |
| **Web / URL** | `web` | trafilatura → `markdown_to_ir(extractor_name="html")` (`content/pipeline/jobs.py:535-540`) | none | the full HTML |
| **Image (PNG/JPG)** | `image` (`ingest/resolution.py:46-47`, `0b480dd851`) | GLM-OCR only, upload OK always required, no fallback (`content/pipeline/jobs.py:249-257`, `:283-312`; `ingest/extractors/__init__.py:185`) | as PDF | the file |
| **Phone photo** | not a source: re-encoded to PNG into the same originals store with `capture_inbox` and `capture_routes` rows (`capture/inbox.py:53-180`); its `quick_add` route needs an already-imported source (`learnloop_sidecar/handlers/ingest.py:1423`) | — | — | — |
| **Transcript** | `.vtt`, `.srt`, or a text file that sniffs as one (`ingest/resolution.py:17`, `:67`; `ingest/transcripts.py:48`); there is no pasted-text path | `parse_transcript` → `transcript_to_ir` (`content/pipeline/jobs.py:542-552`) | none | the file |
| **Audio** | `audio` | `transcribe_audio` with the `[ingest.audio]` endpoint (`ingest/transcription.py:67-90`), from `_extract_audio_transcription` (`content/pipeline/jobs.py:913`); not wrapped in `model_call` | transcription | the file |

### 2.3 Re-read

1. **Entry:** the book's "text recognition" action (`learnloop_sidecar/handlers/first_run.py:332`, `:434-460`) → `reread_plan` (`content/pipeline/reread.py:594`) → `enqueue_add_source(source_id=...)`.
2. `handle_import` reads the revision's own bytes, so the revision is the same; the new engine changes the identity, so a new extraction run lands on that revision.
3. `carry_over` (`content/pipeline/reread.py:396`): span aliases (`record_aliases`, `content/sources/span_aliases.py:248` → `reanchor_spans`, `ingest/reanchor.py:41` → `INSERT OR IGNORE source_span_reanchors`, `db/repositories.py:20331-20356`); section progress by a unit map (`content/pipeline/reread.py:211`); the unit selection without exam marks; annotations (`:366`). Citations aren't rewritten: they resolve lazily through the alias authority (`content/sources/span_aliases.py:345-359`).
4. **Re-read never touches `source_unit_inventories`** (no mention in `reread.py`, `span_aliases.py`, `revision_refresh.py` or `reanchor.py`). The next inventory job reuses a row only on the same unit id, unit semantic hash, schema, prompt label, provider and model (`db/repositories.py:20603-20640`); an unchanged unit's row is rebound to the new extraction on conflict (`:20553-20560`). A unit whose text changed gets a fresh, paid inventory row, which synthesis then ignores (§7, KX3).
5. **New bytes** (`refresh_revision`, `content/pipeline/revision_refresh.py:79`): re-anchors, marks `entity_source_links` `needs_reanchor` or `stale` (`:136-149`), records `content_events`, on confirm rewrites **[Y]** `sources/source_sets.yaml` (`:200-230`), and can run an append with `new_revision_ids=[new]` (`:157-170`), the only caller that pins the append's scope (§7).

### 2.4 Inventory

1. The planner enqueues `inventory` with `{extraction_id, units:[{unit_id, role}]}` (`content/pipeline/add_source.py:1649-1651`).
2. `handle_inventory` (`content/pipeline/jobs.py:1488`, 237 lines) prepares each unit's windows (20k-token input windows), runs them on a two-worker pool (`:1644`), routes every SQL write to the runner thread through `_RunnerMailbox` (`:1411`), and checkpoints each window as it lands (`inventory_window`, `:1626`; key `inventory_window_key`, `content/synthesis/source_unit_inventory.py:715`: purpose, **rendered** prompt, schema version, model settings; no output budget).
3. A unit's merged result is written to `source_unit_inventories` keyed on (revision, unit, unit semantic hash, profile, schema, **prompt label**, provider, model) (`migrations/041_source_unit_inventories.sql:32-33`), `ON CONFLICT ... DO UPDATE` (`db/repositories.py:20553`).
4. Model call: `canonical_ingest` route, `source_unit_inventory_prompt`, result `SourceUnitInventory`. Sep 6 finding 3 (lanes discarding paid work) is fixed by the per-window checkpoints.

### 2.5 The automatic build and bootstrap synthesis

1. **Plan** (`run_auto_study_map`, `content/pipeline/add_source.py:1524`): an earlier attempt's queued build is the answer (`:1536-1538`); the kill switch, a problem set or no text skip or wait; `_choose_scope` (`:1377`) withholds exam material by the one predicate (`exam_material_units`, `:1422`) and picks chapters up to `quick_add_scope_input_tokens` (40,000, `config/schema.py:841`), skipping built units (`covered`); the authoring route must be ready and consented; `decide_cost` may pause (`:1577-1582`).
2. **Write the scope** under `vault_mutation_lock`: **[Y]** `upsert_source_set` writes `sset_quickadd_<source>` with scope = previous ∪ chosen − withheld (`:1588-1626`).
3. **Enqueue** one batch: `inventory` then `bootstrap_synthesis` with `{"source_set_id", "brief", "mode": "auto", "apply"}` (`:1646-1667`). **No `new_revision_ids`, no unit ids for the synthesis job.**
4. **Route** (`handle_bootstrap_synthesis`, `content/pipeline/jobs.py:1836`): `mode=auto` with an applied map for the subject goes to append (`:1865-1872`, §2.6); the test is "any learning object carries the subject" (`content/synthesis/source_append.py:97`), with a second copy of that rule in `content/pipeline/build_plan.py:140`.
5. **Inputs** `_collect_inputs` (`content/synthesis/source_set_synthesis.py:249`): the exam predicate over all source sets (`:263`); per member, the current extraction and its IR; inventories **by revision** (`db/repositories.py:20661`), chosen per unit by `_best_inventory` (`content/synthesis/source_set_synthesis.py:225`, §7 KX3); exam units feed only the exam profile, held-out spans go to the leakage gate.
6. **Manifest before the run** (`:2207`): `build_manifest` (`content/synthesis/synthesis_manifests.py:142`) hashes 20 fields (`:35-56`), including `facet_identity` and `graph_nomination` dumps in `scope`, the budgets, `algorithm_version` and three vault snapshot hashes. **Persisted** `synthesis_manifests`; its hash is the agent run's `input_context_hash` (`content/synthesis/source_set_synthesis.py:2226`).
7. **Reuse** a completed run with the same hash (`_reusable_bootstrap_run`, `content/synthesis/source_set_synthesis.py:1978`, called at `:2230`) and apply its proposal if asked (`:2244`; Sep 6 finding 7 fixed here). Otherwise **persist** `agent_runs` (running) and `synthesis_runs` (`:2252-2268`).
8. **Shards** (`_run_synthesis`, `:2791`): inventories packed into shards of `synthesis_shard_input_tokens` (40,000) by `_shards` (`:460`); each shard's pass is checkpointed (`_shard_checkpoint_key`, `:3035`, and `synthesis_pass` checkpoints, `:2855`); a total-input preflight counts only passes that will run (`:2836-2838`); each pass runs under `generation_limit` (`:2849`) and is saved before its budget check. One span-request round (`:2883`) may follow.
9. **Concept-graph structuring** (`_model_graph_structuring`, `:3164`): one call over the merged candidate, skipped with a recorded reason at the input ceiling or a zero budget (`:3212-3245`), **not checkpointed** (`:3255`); registry merges are recorded in `judgment_ledger` before use (`:3262-3283`).
10. **Facet identity** (`_facet_identity_plan`, `:2042`; §2.7), then the candidate is saved (`save_synthesis_candidate`, `:2285`).
11. **Normalize, gate, persist** (`_gate_and_persist`, `:2362`): `_normalize` (`:659`, §1.1), `run_synthesis_gates`, the instrument gates (persona gate: one structured call per persona per diagnostic item, `content/authoring/persona_gate.py:540-548`, uncheckpointed, falling silently to a string comparison on any provider error, `:549-551`), then `persist_proposal_batch` → `proposal_batches` and `proposed_patch_items`; `facet_identity_actions` rows as `proposed`.
12. **Apply** (`_apply_and_wire_goal`, `content/synthesis/source_set_synthesis.py:3727`) through `apply_accepted_items` (§2.8) when `apply` and the gate (`auto_apply_allowed`, `content/pipeline/add_source.py:1078`) allow.
13. **Epigraphs**: one uncheckpointed call per run (`content/synthesis/vault_epigraphs.py:66`).

### 2.6 Keep-ahead and chapter appends

1. **Trigger:** the Reader reaches a section → `keep_ahead_for_reader` (`content/pipeline/add_source.py:2015`) → `advance_reading_build` (`:1998`) → `plan_reading_advance` (`:1831`) → `act_on_reading_request` (`:1864`) → `request_auto_build(chapter_ids=...)` (`:1717`) → `DurableIngestJobs.enqueue_auto_build`. A reading sweep thread retries failed requests (`content/pipeline/jobs.py:3971`, `:4511`); `reconcile_reading_builds` (`content/pipeline/add_source.py:1795`) catches up at bind.
2. The planner runs as in §2.5 steps 1-3, so the scope grows and the batch is again `inventory` → `bootstrap_synthesis{mode: auto}` with no new revision or unit ids.
3. `handle_bootstrap_synthesis` sees an applied map and calls `handle_append_synthesis` (`content/pipeline/jobs.py:1872`), which passes `new_revision_ids=payload.get(...) or None` (`:1989`), so **`None`**.
4. `_append` (`content/synthesis/source_append.py:224`): `revs = set(new_revision_ids or inputs.selected_revision_ids)` (`:249`), so the book's one revision, and `new_inventories` = **every inventory of every scope unit** (`:250`). The neighbourhood is bounded (`append_neighborhood_input_tokens`, 24,000; `:262-267`); the new inventories are not.
5. **Manifest** (`:290`) with `scope = {mode, change_kind, new_revision_ids, neighborhood, facet_identity}` (`:274-289`); `revision_diff` is not in it. **Reuse** returns the old proposal and **never applies it** (`:320-327`; Sep 6 finding 7, still open here).
6. **Model call:** `request_append_reconciliation` (`:84`), purpose `append_reconciliation`, result `AppendReconciliation`, through `execute_structured_operation` with **no checkpoint, no `generation_limit` and no input ceiling**; an over-budget output is rejected after generation (`:557-558`) by `_output_tokens`, which escapes non-ASCII (`:571-575`). A span-request round may make a second call (`:560-568`).
7. Facet identity (`:392-398`), `_normalize_append` (`:583`) → `_normalize` plus provenance links and notation mappings, gates, instrument gates, persist (`:446`).
8. **Auto-apply** only provenance links that pass `_auto_applies` (`:679-681`); every concept, facet and LO stays a pending review item (`:487-488`), so the card says "N changes need a look" (§7, KX4). Then the near-duplicate facet doctor (review only, `:510-518`) and epigraphs (`:524`).

### 2.7 Facet identity and the mint gate

1. `_facet_identity_plan` (`content/synthesis/source_set_synthesis.py:2042-2064`) returns `None` with the switch off and turns any exception into `status="error"`; bootstrap and append both call it.
2. **Groups** (`build_plan`, `content/facet_identity/plan.py:169`): union-find over same concept, graph edges, lexical Jaccard ≥0.85 and an embedding top-k (`content/facet_identity/grouping.py:125-210`; embeddings are off by default); oversized groups split (`:211`, `:259`); attach groups pair survivors with registered facets (`content/facet_identity/plan.py:317-407`).
3. **Judge:** `resolve_route` (`content/facet_identity/judge.py:1144`) and `build_judge` (`:1180`) pick the Decider or the LLM judge; a route that fails to build becomes `judge_unavailable` (`:1199-1204`; `content/facet_identity/plan.py:247-250`). Checkpoints: the LLM judge's key includes the output budget (`content/facet_identity/judge.py:710-721`), the Decider's doesn't (`:974-979`). Caps (`:1220-1230`): on a spend limit, the group and every later group are `not_run` (`:756-759`), so which groups get judged depends on group order; those candidates fall through to D2.
4. **Merge, absorb or keep distinct** under the judge's rules (`:107-138`), repaired by `validate_partition`; owner `different` verdicts veto (`:520-569`).
5. **Mint or alias** inside `_normalize` (§1.1 stages 3-6): judge retirees aren't minted; survivors take the union through `facet_meaning.join_candidate` (alias-only when the meaning check refuses); the rest go to D2 `judge_facet_mints` (`content/synthesis/facet_mint_gate.py:386-417`): MINT, ALIAS (no facet row; an alias) or ABSTAIN (minted as `proposed`).
6. **Persistence:** merged or shortlisted pairs → `judgment_ledger` task `same_facet` (`content/facet_identity/judge.py:450-514`); actions → `facet_identity_actions` as `proposed` (`content/facet_identity/actions.py:598-615`); aliases → **[Y]** `facets.yaml` `aliases` on the survivor through a proposal `update` row (`content/synthesis/source_set_synthesis.py:1078-1170`). The applied status of an ingest action is derived from `facets.yaml`, never written.
7. **Undo** (`undo_action`, `content/facet_identity/actions.py:1711`): under the lock, refuses if the survivor changed since, checks the meaning rule before writing an intent, records `undoing` with owner `different` verdicts, then `_finish_undo` restores the file (`:1867-1900`).

### 2.8 Proposals: patch to apply, recovery and undo

1. `apply_accepted_items` (`content/proposals/patches.py:70`) checks span support before the lock (`:92`), then under `vault_mutation_lock` (`:93`): dependency statuses (`:167-172`) → accept-time rechecks (`:181`) → stage the YAML into a temp copy (`content/proposals/apply_protocol.py:146-210`) → verify the registry transition (`content/proposals/patches.py:198-203`) → **insert the intent** into `apply_intents` (`:205-211`) → `materialize_targets`: temp file, fsync, `os.replace`, one file at a time (`content/proposals/apply_protocol.py:330-358`) → `sync_vault_state` (`content/proposals/patches.py:216`) → `perform_db_effects` (`:217`) → mark the intent applied (`:218`) → `record_content_recalibration` (`:237-245`).
2. **Recovery** (`recover_apply_intents`, `content/proposals/apply_protocol.py:576`) re-materializes, syncs, re-runs the effects and marks applied. **Its only caller is `doctor --fix-state`** (`ops/doctor.py:181`, `:1309-1345`); the module docstring says "Startup/doctor recovery" (`content/proposals/apply_protocol.py:19-20`), and the maintenance feed's "Complete pending apply" action (`ops/maintenance_feed.py:211`) has no handler in the sidecar or the desktop. The sidecar recovers facet actions only (`learnloop_sidecar/context.py:208-211`).
3. **Recovery writes over newer YAML.** Each intent records a `pre_hash` per file (`content/proposals/apply_protocol.py:237-243`) that nothing reads; `materialize_targets` skips a file only when it already equals `post_hash` (`:342`), and otherwise writes the intent's content over whatever the file holds now.
4. **Crash windows** (each between two writes):
   - W1, statuses written, no intent (`content/proposals/patches.py:167-205`): benign.
   - W2, intent committed, files partly renamed (`:205-213`): the vault is half new and the database untouched; the sidecar serves the partial vault, and the next accept doesn't look for pending intents (`pending_apply_intents` is read only by recovery, doctor and the feed).
   - W3, YAML written, not synced (`:213-216`): projections stale, items still pending.
   - W4 and W5, mid-effects or effects done but unmarked: idempotent (`content/proposals/apply_protocol.py:390-392`, `:420-436`).
   - W6, marked applied, before recalibration (`content/proposals/patches.py:218-245`): never recovered, because recovery omits recalibration (`content/proposals/apply_protocol.py:591-596`).
5. **Undo of a proposal** (`reject_applied_items`, `content/proposals/patches.py:316-347`): under the lock, with no write-ahead intent; LO creates go dormant, practice items get a database flag, concepts and edges are deleted (`:1136-1267`); facet items can't be reverted here (`:1151-1152`). The book's one-tap Undo (`undo_source_questions`, `content/pipeline/add_source.py:2082`) bumps the build generation, cancels queued work, rejects every applied item and records the verdict in `judgment_ledger` (`:2044`).

### 2.9 The Reader's import and the canonical import

| | the Reader's import | the canonical import |
|---|---|---|
| job | `reader_exercise_import` (`content/pipeline/jobs.py:3232`) | `source_exercise_import` (`:3342`) |
| exam check | held-out spans only, in the handler, before any model call (`:3253-3262`); a syllabus refuses (`:3259-3264`) | through `exercise_statements` and the exam predicate (K1 D4) |
| authoring | `exercise_authoring.import_exercises` (`content/authoring/exercise_authoring.py:465`, 401 lines); idempotent by a prompt-level dedupe | `_import_source_exercise` (`content/authoring/source_exercise_import.py:1144`, 241 lines): author, check within a time box, write with `canonical_exercise` and the key's status |
| key check | `record_reader_import` rows, then a plain background thread verifies keys (`content/pipeline/jobs.py:3322`), outside the job's write guard | the ladder under a `judgment_work_claims` lease with its own heartbeat thread (`content/authoring/source_exercise_import.py:781-806`) |
| writes | **[Y]** practice items directly (both are in `APPLYING_JOB_TYPES`, `content/pipeline/jobs.py:3941`) | the same |

The **legacy canonical lane** (`legacy_ingest`, `exam_ingest`) is a third synthesis lane, still live: the Ingest screen's legacy and exam modes and `learnloop ingest` reach it (`content/pipeline/jobs.py:4625`, `cli/runtime.py:417`). Its windows are checkpointed (`legacy_ingest_window`, `content/pipeline/source_ingestion.py:502`), and its run reuse key now includes instructions, subject and provider (`canonical_ingest_context_hash`, `:980`; Sep 6 finding 8 fixed).

### 2.10 Retry and resume after a crash or a model failure

| failure | what survives | what's paid again |
|---|---|---|
| process dies mid-job | the job's lease expires; startup and each drain tick fail it as interrupted (`content/pipeline/runner.py:730`, `:771-836`); the learner resumes | every checkpointed call is reused: GLM windows, inventory windows, synthesis passes, judge groups, legacy windows |
| bootstrap fails after the shards | the candidate is saved before the gates (`content/synthesis/source_set_synthesis.py:2285`); `retry_synthesis(reuse_candidate)` revalidates with zero calls (`content/pipeline/jobs.py:1876-1880`; `revalidate_synthesis_candidate`, `content/synthesis/source_set_synthesis.py:2617`) | the structuring pass, persona fire calls and epigraphs if the run is re-made |
| append fails (gate, budget, provider) | nothing: no candidate, no checkpoint | **the whole append call, and its span round**; an over-budget output fails the same way on every retry |
| provider rate limit or outage | the transport's own retries (SDK retries off, `ai/providers/openai_chat.py:293`; Sep 6 finding 5 fixed) | per call |
| truncated output | `finish_reason == "length"` is detected (`ai/providers/openai_chat.py:582`; Sep 6 finding 6 addressed) | the call |
| apply crashes | the intent, recovered only by `doctor --fix-state` (§2.8) | none, but see W2 and W6 |

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KD1 | high | **Keep-ahead appends re-send the whole book so far** (§7 KX1). | `content/pipeline/add_source.py:1646-1667`, `content/pipeline/jobs.py:1989`, `content/synthesis/source_append.py:249-250` |
| KD2 | high | **Apply recovery can overwrite newer YAML, and runs only under `doctor --fix-state`.** `pre_hash` is recorded and never read; a crash between renames leaves a half-applied vault that the sidecar serves and the next accept builds on. The docstring promises startup recovery that doesn't exist. | `content/proposals/apply_protocol.py:19-20`, `:237-243`, `:342`, `:576`; `ops/doctor.py:1309-1345` |
| KD3 | medium | **A durable arXiv import reads only the abstract page.** `default_fetch` maps arXiv to `website_page` and fetches `/abs/`; only a `/pdf/` URL reads the paper. Inventories and synthesis then see the abstract. | `content/pipeline/jobs.py:110`; `ingest/resolution.py:52-54` |
| KD4 | medium | **Three synthesis lanes** (legacy windows, bootstrap, append) and **two exercise-import lanes** with different exam checks, key-check concurrency and authoring code. | §2.5, §2.6, §2.9 |
| KD5 | medium | **The persona gate falls back to a string comparison on any provider error, silently,** inside every bootstrap and append's instrument gates. | `content/authoring/persona_gate.py:540-551` |
| KD6 | low | **No pasted-transcript path, and the phone photo isn't a source.** Transcripts must be files; a photo's quick-add needs a source imported elsewhere. | `ingest/resolution.py:17`, `:67`; `learnloop_sidecar/handlers/ingest.py:1423` |
| KD7 | low | **The extraction request hash contains the revision's ULID,** so the same bytes in two vaults (or after a sync) never share an extraction cache entry. | `ingest/hashing.py:61-86` |

## 3. Boundaries, duplicated predicates, jobs and leases, checkpoints

### 3.1 Where the stages meet, and what each boundary passes

| boundary | what crosses | can each side change alone? |
|---|---|---|
| extraction → inventory | the planner's payload `{extraction_id, units:[{unit_id, role}]}` (`content/pipeline/add_source.py:1649-1651`); inventory rows keyed on revision, unit id and unit semantic hash (`migrations/041_source_unit_inventories.sql:32-33`) | **No.** Unit ids are ordinal per extraction; a re-read that renumbers units re-pays every inventory, and nothing on either side records which extraction a unit id came from beyond the row's rebinding (`db/repositories.py:20553-20560`). |
| inventory → synthesis | inventories **by revision** (`db/repositories.py:20661`), picked per unit by `_best_inventory` (`content/synthesis/source_set_synthesis.py:225`); the manifest records only `"schema|prompt"` labels per `revision:unit` (`:358-361`, `:379-381`) | **No.** Synthesis ignores the row's extraction, semantic hash, provider and model, and labels each entry with the *current* extraction id (`:365`, `:397`), so an inventory change (prompt, model, re-read) doesn't reach synthesis, and synthesis can't say which row it used. |
| synthesis → facet identity | the merged candidate in, a `FacetIdentityPlan` out (`:2042`); the plan's retirements are consumed inside `_normalize` (`:884-920`) | **Partly.** The judge is its own package, but applying its verdicts is stage 4-6 of `_normalize`, and the subpackages import each other both ways (§1.2). |
| synthesis → apply | `proposed_patch_items` rows with client ids, plus a list of auto-apply ids (`content/synthesis/source_append.py:454`, `:487`) | **Yes, mostly.** The row vocabulary is the contract; apply knows nothing of synthesis. The weak point is apply itself (§2.8). |
| pipeline → retrieval | after an extraction, `jobs.py` imports nine `source_retrieval` modules to ask each derived index whether it's owed a job (`source_vectors`, `local_index`, `fallback_space`, `section_coverage`, `student_encoder`, `feedback`, `dense`, `spaces`, `corpus`) | **No.** Each new derived index adds a job type, a handler and its import to `jobs.py` (`content/pipeline/jobs.py:2282-2301`, `:3928-3931`). |
| pipeline → exam predicate | the planner, synthesis, the Reader's import and the canonical import each call `content/sources/exam_material.py` directly (`content/pipeline/add_source.py:1422`, `content/synthesis/source_set_synthesis.py:263`, `content/pipeline/jobs.py:3256`) | One predicate, several doors: K1's finding, not repeated here (`docs/reviews/refactor-k1.md`). |
| desktop → sidecar | about 31 RPC methods from six components (`IngestScreen.tsx`, `OutlineAndPlan.tsx`, `IngestActivity.tsx`, `AddToCollection.tsx`, `SourceLibrarySidebar.tsx`, `FacetIdentityPanel.tsx`) through `METHOD_REGISTRY` (`learnloop_sidecar/registry.py:20-33`) | **No:** the frontend re-implements at least eight backend rules (§3.2). |

### 3.2 Duplicated predicates

| predicate | copies | disagree? |
|---|---|---|
| which inventory to use | `_best_inventory`, `content/synthesis/source_set_synthesis.py:225` and `content/synthesis/source_coverage.py:42` (same body) | no, both pick the oldest (§7) |
| create or update ("does the subject have a map?") | `subject_has_applied_study_map`, `content/synthesis/source_append.py:97`; `subject_has_study_map`, `content/pipeline/build_plan.py:140` ("the single routing rule", `:143-144`) | same rule today, two copies; the Build a Study Map note describes a third version (§8) |
| token estimate of JSON | `_shards` (`content/synthesis/source_set_synthesis.py:467`, escapes non-ASCII), `_output_tokens` (`content/synthesis/source_append.py:571-575`, escapes), `_result_tokens` (`content/synthesis/source_set_synthesis.py:2974`, doesn't: "would overcharge CJK or math-symbol output") | **yes**: maths-heavy text gets more, smaller shards and a tighter append budget than bootstrap's passes |
| assessment-only roles | `content/sources/role_authority.py:217` `{exam}`; `apps/learnloop-tauri/src/components/OutlineAndPlan.tsx:38` `{exam, problem_set}`; role lists copied in `OutlineAndPlan.tsx:26-36` and `AddToCollection.tsx:14-24` | **yes** |
| retry-synthesis eligibility | `content/pipeline/jobs.py:5346-5355` (failed, blocked or cancelled, every inventory complete); `apps/learnloop-tauri/src/components/IngestActivity.tsx:351-355` (failed only) | **yes**: a cancelled synthesis is offered "resume", not retry |
| budget bounds | `learnloop_sidecar/handlers/ingest.py:34-41` (`BUDGET_BOUNDS`, whose comment says the frontend reads them); hard-coded in `IngestActivity.tsx:364-372`, `:548-576` | copies; `OutlineAndPlan.tsx:867-888` does read them |
| source kind | `ingest/resolution.py:11-72`; `apps/learnloop-tauri/src/screens/IngestScreen.tsx:37-50` (cites a file that doesn't exist), whose classifier map omits `image` (`:716-723`), as does `dto.ts:3313` | **yes** for images |
| native-PDF page ranges | `learnloop_sidecar/handlers/ingest.py:193-194` (allowed when native is unready and fallback is on); `IngestScreen.tsx:598-599`, `:1208-1211` (never) | **yes** |
| page-range parsing | `learnloop_sidecar/handlers/ingest.py:338-361`; `apps/learnloop-tauri/src/components/PageRangeSelector.tsx:4-18` | copies |
| "an import finished" | `IngestActivity.tsx:95-105` tests `jobType === "import_source"`, which no job has; it works through a regex on the workflow name | latent |
| `detect_source_kind` | `ingest/detect.py:6` (the new categories; tests only) and `content/pipeline/source_ingestion.py:669` (legacy kinds; no caller in `src`) | not duplicates, but two dead-ish wrappers with one name |
| lease heartbeat | `content/authoring/source_exercise_import.py:781-806` and `source_retrieval/reading_paths.py:819-841` are the same function with different constants (§3.3) | copies |

### 3.3 Job and lease mechanisms

**The coverage audit's "four reimplementations" holds, and undercounts.** In scope or touching it there are **six lease stores** and **five threaded heartbeat loops**:

| | mechanism | store | heartbeat | on expiry | fencing | clock |
|---|---|---|---|---|---|---|
| A | the ingest drain (`IngestRunner`, `content/pipeline/runner.py:556`; host `DurableIngestJobs`, `content/pipeline/jobs.py:4030`) | `ingest_jobs` (`migrations/033_durable_ingest_jobs.sql`); claim `db/stores/ingest_queue.py:374` under the vault lock | 15 s thread (`content/pipeline/runner.py:567`, `:1126-1151`), TTL 120 s (`:566`) | job **fails** as interrupted; the learner resumes (`:771-795`); expiry runs at startup and each drain tick (`:730`, `:816-836`) | strongest: every write on the job thread passes `guard_ingest_writes` (`:1029`), finish is owner-checked (`db/stores/ingest_queue.py:519-534`); Sep 6 findings 1 and 2 fixed | injected |
| B | shared judge claims (`db/stores/judgment_claims.py:37`) | `judgment_work_claims` | per user (below) | the next claimer takes over with epoch + 1 (`:68-80`) | `complete_claim` owner and epoch (`:103-114`) | per user |
| B1 | canonical key check, on B | | 30 s thread (`content/authoring/source_exercise_import.py:781-806`), TTL 120 s | | `holds_claim` called **without `now`** (`:820`, `:838`), so a lapsed but unclaimed lease still commits | wall, on purpose (`:729-732`) |
| B2 | reading-path judge, on B | | 30 s thread (`source_retrieval/reading_paths.py:819-841`), TTL 300 s | | same gap (`:919`) | wall |
| C | service spend reservations (`source_retrieval/service_spend.py`) | `source_service_spend` | 60 s process-wide thread (`:91-147`), TTL 300 s | reconcile with receipts or release at the next admission (`db/stores/source_service.py:1548`) | process token only, no epoch | **mixed**: reserves with the injected clock (`source_retrieval/service_spend.py:194`), renews with `datetime.now` (`:125`) |
| D | follow-up generation (`followup_run/jobs.py:71`) | `followup_generation_jobs` | **none**, TTL 900 s | re-leased, at most twice | finish only | injected |
| E | phone jobs (`capture/jobs.py`) | `mobile_jobs` | none, no TTL | requeued when the host's boot id differs (`:216-218`) | none (`:163-171`) | — |

Plus the reading sweep thread (`content/pipeline/jobs.py:4511`), three quick-check lanes (`:5518`), the inventory pool (`:1644`), the Reader import's unguarded key-check thread (`:3322`), the Marker and text-layer worker processes, and outside scope the post-attempt jobs, the approach-map claims and the reader requests. The semantics differ: A fails and waits for a person; B, D and E retry by themselves; C reconciles money.

**Two processes on one vault.** The sidecar and a CLI drain can both run A: claims serialize on the vault lock and the single-writer check, and a CLI's stale-lease recovery can fail a desktop job whose heartbeat stalled, since live attempts are tracked per process (`content/pipeline/runner.py:511-548`). The phone host doesn't bind ingest (`learnloop_sidecar/context.py:322-326`) but runs the post-attempt worker on the same vault.

### 3.4 Checkpoints and reuse keys

**Six checkpoint recipes, three run-level reuse keys, and four paid calls with neither** on the ingestion and synthesis path. All six write the same table (`model_work_checkpoints`, through `db/stores/model_calls.py:144-156`); what differs is the key:

| checkpoint | key | prompt identity | output budget in key | settings |
|---|---|---|---|---|
| GLM-OCR window (`ingest/extractors/glm_ocr.py:416-420`) | asset SHA, pages, backend, two model names | n/a | no | backend only |
| inventory window (`content/synthesis/source_unit_inventory.py:715-730`) | `content_key` | **rendered** prompt | **no** ("a validated window is reusable under any budget") | `model_settings` |
| synthesis pass (`content/synthesis/source_set_synthesis.py:3035-3075`) | hand-rolled SHA-256 | **label** (`prompt_version`) plus the inputs: brief, registry index, exam profile, shard, ordinal | **no** ("a retry with revised ceilings ... must survive") | `model_settings` |
| facet judge, LLM (`content/facet_identity/judge.py:710-721`) | `content_key` | rendered prompt plus schema | **yes** ("as everywhere under the policy") | settings, effort |
| facet judge, Decider (`:974-979`) | `content_key` | question set, input hash, instructions, options | n/a | model |
| legacy window (`content/pipeline/source_ingestion.py:502`) | `content_key` | rendered prompt plus schema | no | provider and model only |

| run-level reuse | key |
|---|---|
| bootstrap | the manifest hash = `agent_runs.input_context_hash` (`content/synthesis/synthesis_manifests.py:1-18`, `:35-56`) |
| append | the same recipe (`content/synthesis/source_append.py:320`) |
| legacy | `canonical_ingest_context_hash` (`content/pipeline/source_ingestion.py:980`) |

**No checkpoint and no reuse key:** the append reconciliation and its span round (`content/synthesis/source_append.py:84`), the concept-graph structuring pass (`content/synthesis/source_set_synthesis.py:3255`), the persona fire calls (`content/authoring/persona_gate.py:541`), the epigraphs (`content/synthesis/vault_epigraphs.py:66`). Outside synthesis, the Reader's import dedupes by prompt instead.

`ai/execution.py` already holds the shared pieces (`content_key`, `:175`; `model_settings`, `:179`; `generation_limit`, `:304`; `record_model_calls`, `:276`). Each site composes them differently, and the judge's comment states a policy ("everywhere") that two neighbouring sites contradict in their own comments.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KB1 | high | **The inventory → synthesis boundary loses identity.** Synthesis picks inventories by revision and unit id alone and records labels, so it can neither use nor name the row it used (§7 KX3). | `content/synthesis/source_set_synthesis.py:225`, `:358-397`; `db/repositories.py:20661-20667` |
| KB2 | high | **Six lease stores and five heartbeat loops with different expiry semantics, fencing and clocks;** two are verbatim copies, two commit after a lapse, one mixes clocks, two have no heartbeat. A bug fixed in one (Sep 6 findings 1 and 2, fixed in A) stays in the others. | §3.3 |
| KB3 | high | **Six checkpoint recipes and four uncheckpointed paid calls.** The recipes disagree on whether the prompt is rendered or labelled and whether the output budget belongs in the key; the append, structuring, persona and epigraph calls have none, so a retry re-pays them. | §3.4 |
| KB4 | medium | **The desktop re-implements at least eight backend rules, three of which disagree** (assessment roles, retry eligibility, image kind, native page ranges). | §3.2 |
| KB5 | medium | **Three token estimators**, two escaping non-ASCII and one not. | §3.2 |
| KB6 | medium | **Every derived index is wired through `jobs.py`** (nine `source_retrieval` imports, a job type and a handler each). | §3.1 |
| KB7 | low | Two create-or-update rules, two `_best_inventory`, two `detect_source_kind`, one stale `import_source` test in the desktop. | §3.2 |

## 4. Decision points and what's recorded

**One ADR-017 decision record exists in the whole area:** the AD commission skip that B8 added (`content/pipeline/jobs.py:3408-3447`). Everything else answers "why" (if at all) from five ad hoc stores: `ingest_jobs.result_json` (the planner's outcome), `synthesis_runs.coverage_decisions` and `actual_usage` (gate diagnostics, auto-apply ids, graph nomination, facet-identity plan), `judgment_ledger` (judge pairs, registry merges, Undo verdicts), `facet_identity_actions`, and `source_extraction_runs.health_json`. None carries a trace id that joins the planner's choice to the run it caused to what got applied; the joins are through the batch id, the manifest and the proposal id.

| decision | where | recorded | "why x and not y" from stored data |
|---|---|---|---|
| **extractor** (GLM-OCR, Datalab, Marker, pypdf; fallback) | `ingest/extractors/__init__.py:84`, `:165-211`; `content/pipeline/jobs.py:260-312` | `extractor`, version and `fallback_from` in the extraction run's identity; the selection reason and fallback flags in `health_json` only | **partly**: what ran and what it fell back from; not which candidates were unavailable, since `auto` stays out of the config (`content/pipeline/jobs.py:166-171`) |
| **which chapters to build** (scope) | `_choose_scope`, `content/pipeline/add_source.py:1377` | the planner's `result_json`: chosen unit ids, plan info, cost (`:1628-1640`) | **partly**: what was chosen; not which chapters were withheld as exam material (computed at `:1385`, used to shape the scope, absent from `info`, `:1371-1374`) or skipped as built |
| **pause for money or consent** | `decide_cost`, `:1577-1582`; consent `:1569-1576` | `result_json` outcome `paused` / `waiting` with the reason and cost | **yes** |
| **bootstrap or append** | `content/pipeline/jobs.py:1865-1872` | `synthesis_runs.mode` | **no reason**: the rule ("an LO carries the subject") isn't recorded, and the job keeps its `bootstrap_synthesis` type |
| **which inventory row** per unit | `_best_inventory`, `content/synthesis/source_set_synthesis.py:225` | the manifest's `"schema|prompt"` label per unit | **no**: not the row id, its extraction, semantic hash, model or age; silent |
| **which units an append sends** | `content/synthesis/source_append.py:249-250` | `new_revision_ids` in the manifest scope (revision granularity), the neighbourhood record | **no**: the unit list isn't recorded, so "why did this append carry chapter 1?" can't be answered from rows |
| **reuse a completed run** | `content/synthesis/source_set_synthesis.py:2230`; `content/synthesis/source_append.py:322` | `reused=True` in the job result | **partly**: that it reused, and the manifest hash; not which run, and not that an append reuse skipped the apply |
| **structuring skipped** | `content/synthesis/source_set_synthesis.py:3212-3258` | the reason in the run's usage | **yes**, in a JSON blob no screen shows |
| **judge merge, absorb, keep distinct** | `content/facet_identity/judge.py:107-138` | `judgment_ledger` for merged or shortlisted pairs, with sets, basis and Decider probabilities (`:450-514`) | **yes** for joined pairs; **no** for pairs kept apart without a shortlist (`:488-489`, by owner decision); owner vetoes only in the plan JSON |
| **judge capped or unavailable** | `content/facet_identity/plan.py:247-250`, `:305-313` | plan status in run JSON; a build exception reduced to a string | **partly**; no diagnostic, so the learner sees nothing |
| **mint or alias (D2)** | `content/synthesis/facet_mint_gate.py:386-417` | ALIAS and ABSTAIN as review diagnostics with a typed reason (`:505-550`) | **ALIAS, ABSTAIN yes; MINT silent**; a D2 alias gets no action row and no undo |
| **auto-apply or review** | `_auto_applies`, `content/synthesis/source_append.py:1005-1031`; `auto_apply_allowed`, `content/pipeline/add_source.py:1078-1094` | the chosen ids (`content/synthesis/source_append.py:454`) | **no**: `_auto_applies` returns a bool; the gate's three conditions (switch, apply switch, Undo generation) collapse to one bool; "why did this concept need a look?" has no stored answer beyond "it isn't a provenance link" |
| **items dropped by the normalizer** | `_normalize` items-off guard, unresolved spans, invalid edges | review diagnostics in the proposal | **yes** |
| **persona gate fired or not** | `content/authoring/persona_gate.py:540-551` | the gate's verdict | **no** when the model call failed: the fallback to a string comparison leaves no trace |
| **retry** | `content/pipeline/runner.py:930-944`; `retryable` on `IngestRunnerError` | the job's `error_json` with code and stage | **yes** for what failed; not what a retry will re-pay |
| **Undo** | `content/pipeline/add_source.py:2082` | `judgment_ledger` owner verdict (`:2044`) | **yes** |

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KO1 | high | **The three decisions that set what synthesis reads are silent:** which inventory row, which units an append sends, and why a unit was withheld from a build. A wrong study map can't be traced to its inputs from stored rows. | `content/synthesis/source_set_synthesis.py:225`; `content/synthesis/source_append.py:249-250`; `content/pipeline/add_source.py:1385` |
| KO2 | high | **Auto-apply versus review has no stored reason,** so "N changes need a look" can't be explained per item. | `content/synthesis/source_append.py:454`, `:1005-1031`; `content/pipeline/add_source.py:1078-1094` |
| KO3 | medium | **No trace id joins planner → run → proposal → apply;** "why" lives in five stores and three JSON blobs. Only one ADR-017 record exists in the area. | `content/pipeline/jobs.py:3408-3447`; the table above |
| KO4 | medium | **Silent fallbacks:** the persona gate's provider failure, D2 MINT, kept-apart judge pairs, a capped judge (run JSON only). | the table above |

## 5. Functional core and shell, comments, dead code, onboarding

### 5.1 Core and shell

**Pure cores that already exist, and are the area's best-tested parts:** the D2 mint gate (`judge_facet_mints`, `content/synthesis/facet_mint_gate.py:386`, pure with closed reasons), the synthesis gates (`run_synthesis_gates` over a `GateProposal`, `content/synthesis/synthesis_gates.py`), the exam profile aggregate (`content/synthesis/exam_profile.py`), the extractor normalizers and GLM-OCR's response mapping (`ingest/extractors/normalizers.py`; `responses_to_ir`, `ingest/extractors/glm_ocr.py:1350`), `_shards` (`content/synthesis/source_set_synthesis.py:460`), the manifest hash (`content/synthesis/synthesis_manifests.py:64`), and the facet judge's partition validation.

**Where computation and I/O are entangled, and it costs:**
- **`_collect_inputs`** (`content/synthesis/source_set_synthesis.py:249`) reads SQLite (IRs, selections, inventories) and decides policy in the same loop: the exam predicate, scope-only roles, the merged-unit fallback and `_best_inventory`. The inventory choice (KX3) can't be tested without a database.
- **`_create_study_map` and `_append`** each read the vault, write the manifest, agent run and synthesis run, call the model, normalize, gate, persist, apply under the vault lock and call the epigraph model, in one function (§1.1, KP5). A test of "which items auto-apply" runs the whole append with a fake client.
- **`_normalize`** is close to pure (vault, inputs and `now` in; rows out), except untitled entities' ULID ids. Its problem is size and shared state (KP1), not I/O.
- **`run_auto_study_map`** (`content/pipeline/add_source.py:1524`) mixes the scope decision, consent, cost, a YAML write under the lock and the enqueue. `_choose_scope` (`:1377`) is the decision and could stand alone, but it reads the outline, the exam predicate and coverage from the repository itself.
- **`handle_inventory`** (`content/pipeline/jobs.py:1488`) holds the thread pool, the mailbox, the interrupt group and the model calls together; that is the shell's job, and it is the right place for it.

### 5.2 Comments

- **The why-comments are often good,** for example `content/synthesis/source_set_synthesis.py:821-824` (why facets are judged in two passes), `content/synthesis/source_unit_inventory.py:715-723` (why the key is the rendered prompt), `content/facet_identity/actions.py:1772-1775` (why the meaning check precedes the intent), `content/proposals/patches.py:90-91` (no network call holds the lock).
- **Review tags stand in for reasons.** "review F3", "Codex verification of F6", "second review F5", "T1 landing review round 2" appear about 85 times in `content/pipeline`, 57 in `content/facet_identity`, 33 in `content/proposals` and 17 in `content/synthesis` (regex count). The strategy's comment convention (§2.1) says a comment shouldn't name a review round; here the tag is often the only explanation, e.g. `content/pipeline/add_source.py:1536-1537` ("review F3") and `content/pipeline/jobs.py:353` ("second review F5").
- **Comments that contradict the code:** the apply protocol promises "Startup/doctor recovery" (`content/proposals/apply_protocol.py:19-20`; doctor only, §2.8); the judge's key comment says the output budget is in the key "as everywhere under the policy" (`content/facet_identity/judge.py:711-713`), while the inventory and shard keys exclude it on purpose (§3.4); `BUDGET_BOUNDS`'s comment says the frontend reads it (`learnloop_sidecar/handlers/ingest.py:34`; one of three components does); `ingest/detect.py`'s docstring lists five kinds of the eight `resolve_source` returns; `IngestScreen.tsx:37` cites a module that doesn't exist.
- **The long functions lack an approach paragraph:** `_normalize`, `_append`, `_create_study_map` and `handle_inventory` start with one-line or no docstrings.

### 5.3 Dead and near-dead code

| what | evidence | status |
|---|---|---|
| `ingest/fetchers.py`'s fetch path (`fetch_source`, `_FETCHERS`, `fetch_web`, `fetch_arxiv`, `fetch_pdf`, `fetch_textfile`, `fetch_youtube`; about 300 of its 400 lines) | production imports only `youtube_oembed_metadata` and `youtube_video_id` (`content/pipeline/jobs.py:142`, `learnloop_sidecar/handlers/reader.py:1837`); the package re-exports `fetch_source` (`ingest/__init__.py:12`) and only `tests/test_ingest_fetchers.py` calls it. **Its `fetch_arxiv` reads the Atom API and the full text, which the live import doesn't (KD3).** The live fetch is a different function with the same name, `content/pipeline/source_ingestion.py`'s `fetch_source` | test-only, name collision |
| `ingest/detect.py` | tests only (`tests/test_ingest_detect.py`) | test-only |
| `source_ingestion.detect_source_kind` (`content/pipeline/source_ingestion.py:669`) | no caller in `src` | dead |
| `KNOWN_JOB_TYPES`, `KNOWN_WORKFLOW_TYPES` (`content/pipeline/runner.py:106-127`) | one test reads the first | stale |
| `asset_hashes`, `extractor_versions`, `lock_fingerprint` in the manifest (`content/synthesis/synthesis_manifests.py:39`, `:48`, `:54`) | hashed, never passed (`build_manifest` callers, `content/synthesis/source_set_synthesis.py:2211`, `content/synthesis/source_append.py:290`) | always null |
| `pre_hash` in apply intents (`content/proposals/apply_protocol.py:237-243`) | written, never read | dead field with a job to do (KD2) |
| "Complete pending apply" maintenance action (`ops/maintenance_feed.py:211`) | no handler | dead end for the learner |
| Codex names in the job host (`interrupt_codex`, `content/pipeline/jobs.py:5446`) | ADR-018 retired the transport | naming only (not verified further) |

### 5.4 Onboarding: what a new contributor must read to add a thing

| to add | must read today |
|---|---|
| a source type | `ingest/resolution.py`; `content/pipeline/jobs.py` (`default_fetch`, `_is_document`, `default_extract`, `default_extraction_identity`, about 900 lines between them); `content/pipeline/add_source.py` (`_KIND_NOUN`, the missing-file list); `content/pipeline/source_ingestion.py` (the legacy mapping); the frontend's kind tables in four files (§6) |
| an extractor | `ingest/extractors/__init__.py` (the selection ladder and fallback), `content/pipeline/jobs.py` (`_document_extractor`, consent, checkpoints), `ingest/hashing.py` (identity), `content/pipeline/add_source.py` (consent copy, status lines) |
| a synthesis pass | `content/synthesis/source_set_synthesis.py` (3,811 lines: the orchestrator, `_run_synthesis`, the checkpoint, the manifest scope) **and** `content/synthesis/source_append.py` (the second orchestrator), plus `ai/routing.py` and `content/synthesis/ai_contracts.py` |
| a facet rule | `content/facet_identity/judge.py` (rules), `authority.py` (the meaning chokepoint), `plan.py`, and `_normalize` stages 3-6 |

The concepts a newcomer meets before any of these: revision, extraction, unit, span, inventory (and its profile), source set and scope, manifest, agent run, synthesis run, shard, pass, candidate, proposal batch, apply intent, facet identity action, judgment ledger, the exam predicate's partitions, job, batch, lease, attempt generation, checkpoint, keep-ahead request. About two dozen, most of them real; the cost is that the same idea (identity, lease, checkpoint) has several implementations.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KF1 | medium | **The inventory choice and the append's unit choice sit inside I/O-heavy functions,** so the two decisions behind KX1 and KX3 have no database-free test seam. | `content/synthesis/source_set_synthesis.py:249`; `content/synthesis/source_append.py:224` |
| KC1 | medium | **Review tags stand in for reasons in about 190 places,** and five comments contradict the code. | §5.2 |
| KN1 | medium | **A test-only fetch module reads arXiv better than the live import,** under the same function name as the live fetch. | §5.3 |
| KN2 | low | Dead fields and names: three always-null manifest fields, `pre_hash`, a stale job vocabulary, two `detect_source_kind`. | §5.3 |

## 6. Change cost, counted

Counts are from `git show --name-only` on the commits named; "plumbing" (generated vault notes, lock files, pins) is counted apart from behaviour. Frontend means `apps/`.

| kind | real change | behaviour files (src / tests / frontend) | plumbing | why so many |
|---|---|---|---|---|
| **(a) a new source type** | audio, `22d319783a` + `c6c384add4` + `16a65f509f` (Jul 22 - Sep 2) | 11 / 10 / 0 | 0 | the kind lives in `resolution.py`, the fetch mapping, `_is_document`, `default_extract`, `default_extraction_identity`, the native ladder and the legacy mapping |
| (a) | image, inside the GLM-OCR stage (first-parent diff of merge `fcf7dc95d3`) | 18 / 7 / 10 (with the extractor below) | 1 generated, 1 lock, 4 docs | plus the frontend's kind tables: `IngestScreen.tsx:36-60`, `:716-723`, `:952`, `dto.ts:3313`, `useSourceFileDrop.ts:7-8`, `useGlobalAdd.ts:10`, which still omit `image` in two places (§3.2) |
| **(b) a new extractor** | GLM-OCR: `0b480dd851`, `c040c98031`, `70866da163`, `267e801569`, `3556a49772`, `3c2bd21240` (Oct 13-14) | 31 / 7 / 8 commit-by-commit (18 / 7 / 10 net) | **743 generated notes** in two commits (373 + 370, mostly commit stamps), 1 lock | the selection ladder (`ingest/extractors/__init__.py`), consent and checkpoints in `jobs.py`, status and consent copy in `add_source.py`, settings, the sidecar's first-run and ingest handlers, the acquisition preview, `source_refs`, the IR |
| **(c) a new synthesis pass** | epigraphs, `ee2e43120c` (Sep 3) | 9 / 8 / 0 | 0 | **both orchestrators** (`source_set_synthesis.py`, `source_append.py`), the contracts, routing, `repositories.py`, `table_roles.py`, a sidecar handler |
| (c) | T5 graph nomination, `6c6416d3ca` + `5db6cb6227` (Oct 12) | 18 / 7 / 0, then 2 / 1 / 0 the same day to put it into the bootstrap identity | 0 | both orchestrators, the gates, the facet doctor and candidates, config schema and template, the CLI, doctor; the fix shows the manifest-identity trap (a new input isn't in the hash unless someone adds it) |
| **(d) a new facet rule** | exam authority where a facet's meaning is written, `10415fdfc4` (Oct 13) | 8 / 7 / 0 | 0 | `authority.py`, `actions.py`, `apply_protocol.py`, `patches.py`, `role_authority.py`, **both orchestrators** and the gates |
| (d) | span check before a reword applies, `b3dca2b050` (Oct 13) | 5 / 7 / 3 | 0 | `authority.py`, `actions.py`, `span_support.py`, `apply_protocol.py`, `patches.py` |
| identity plumbing | arc C's retired-field fix, `b77257f189` (Nov 11): removing an unread config field moved the synthesis cache key | 9 / 1 / 0 | `config/retired.py` | every whole dump beside a compared hash had to dump the field back; K0 now pins them |

**The two orchestrators' tax.** Since Oct 1, 12 of the 15 commits that changed `content/synthesis/source_append.py` also changed `content/synthesis/source_set_synthesis.py`. The append copy's own comments record three invariants it once lacked: practice items authored regardless of `as_you_read` (`content/synthesis/source_append.py:375-380`), no instrument gates (`:426-428`), and the items-off guard bypassed "by omission" (`:594-596`).

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KH1 | high | **A synthesis-wide change edits both orchestrators, and the append copy has missed invariants three times.** | the table; `content/synthesis/source_append.py:375-380`, `:426-428`, `:594-596` |
| KH2 | medium | **A source type touches about seven places in `jobs.py` and friends and six frontend tables;** two of the frontend tables still lack the last type added. | §3.2; the table |
| KH3 | medium | **A new extractor costs hundreds of generated-note changes** (743 for GLM-OCR) beside about 30 behaviour files. | `3c2bd21240`, `267e801569` |
| KH4 | medium | **Any new synthesis input must be added to the manifest by hand or reuse goes wrong,** and any removed config field moves it unless retired (§7 KX5). | `6c6416d3ca` then `5db6cb6227`; `b77257f189` |

## 7. The K3 candidates

Spend comes from backup-API copies of the Nov 9 backup (`learnloop.db.copies.copy_tree_with_databases`), read on Nov 11 and deleted after; per-vault numbers are only in the gitignored `fixtures-local/k2/spend.md`. **No receipt in any copy has a synthesis, append, inventory, structuring, judge or epigraph purpose:** receipts start in late October and every canonical synthesis in the copies ran in July, and **keep-ahead (landed Oct 13, `ba24b75411`) never ran on the copied vaults** (no `auto_study_map` job in any). So the spend below is measured where the copies allow (one July append and one bootstrap from `agent_runs`) and projected from the copies' inventory sizes elsewhere.

| ID | candidate | verdict | evidence at `565aee8724` | spend |
|---|---|---|---|---|
| KX1 | **keep-ahead appends re-send the whole book** | **confirmed, and wider than stated:** it's the inventories of every scope unit, not just "the book so far"'s revision. The planner enqueues `bootstrap_synthesis{mode: auto}` with no `new_revision_ids` and no unit ids (`content/pipeline/add_source.py:1646-1667`); `handle_append_synthesis` passes `None` (`content/pipeline/jobs.py:1989`); `_append` falls back to every selected revision (`content/synthesis/source_append.py:249`) and takes every inventory of it (`:250`); the scope is previous ∪ new (`content/pipeline/add_source.py:1599-1600`). Only `revision_refresh` pins the scope (`content/pipeline/revision_refresh.py:162`). | **projected, order of magnitude:** append input grows linearly with chapters built, so a book's total is quadratic. The copies' inventories run 2-7 times the source text they summarise; on the one copied source large enough for two builds, the second build's append would carry about 3.7 times the inventory tokens of its new units alone. For a whole textbook (about 35 builds at the 40k cap) that is roughly 10^7-10^8 inventory input tokens against 10^6-10^7 with only new units, and the last appends would exceed any route's context. Not observed: keep-ahead hasn't run on the copies. |
| KX2 | **append has no checkpoint, input ceiling or output split** | **confirmed.** `request_append_reconciliation` calls `execute_structured_operation` with no checkpoint (`content/synthesis/source_append.py:84-93`); no `generation_limit` or `declared_budgets` anywhere in the module; only the neighbourhood is capped (`:262-267`); the output check runs after generation (`:557-558`, `:567-568`) with `_output_tokens` escaping non-ASCII (`:571-575`); a failure leaves no candidate (§2.10). Retry re-pays and, for a deterministic over-budget output, fails the same way. | **measured once:** one July append on a copy cost about 3×10^4 input and 4×10^3 output tokens, and a failed append before it recorded zero (failed runs don't keep usage). With KX1, each retry of a late append re-pays the whole book's inventories. |
| KX3 | **`_best_inventory` reads a unit's oldest inventory** | **confirmed, with a refinement.** Rows come by revision ordered by `unit_id, created_at` (`db/repositories.py:20664`); `_best_inventory` filters by unit and profile only and its stable sort keeps the oldest (`content/synthesis/source_set_synthesis.py:225-235`; same body at `content/synthesis/source_coverage.py:42-55`); the entry is labelled with the current extraction id (`content/synthesis/source_set_synthesis.py:397`). **Refinement:** for an unchanged unit, a new inventory on the same revision overwrites the row and rebinds its extraction (`db/repositories.py:20553-20560`), so the stale case needs a coexisting row with a different semantic hash, prompt label, provider or model: a prompt bump, a model change, or a re-read that changed the unit's text. In those cases the new inventory is **paid for and then ignored**. | **observed shape, no spend:** one copied revision holds inventories from two extractions of the same book (an earlier and a later Marker run); two units' rows are from the earlier one and would be served under the later id. Their semantic hashes match, so no citation is wrong there. The paid-and-ignored case isn't in the copies. |
| KX4 | **appends from chapter 3 on never auto-apply** | **confirmed, and the chapter number is incidental:** every append (any build after the first applied one) auto-applies only provenance links that pass `_auto_applies` (`content/synthesis/source_append.py:679-681`); concepts, facets and LOs from `_normalize` never enter `auto_apply_ids` (`:607`) and stay pending (`:487-488`). Whether that's "chapter 3" depends on how many chapters the first build took. | no spend; learner friction ("N changes need a look"). Auto-applying them is the owner's call (spec §10.2-10.3) |
| KX5 | **the manifest hash is provenance, cache key and reuse key at once** | **confirmed.** The module says so (`content/synthesis/synthesis_manifests.py:8-13`); `agent_runs.input_context_hash = manifest_hash` (`content/synthesis/source_set_synthesis.py:2226`, `content/synthesis/source_append.py:320`). **Over-invalidates:** `task_graph_hash` (every practice item, `content/synthesis/synthesis_manifests.py:111-134`), `algorithm_version` (`:137-140`), token budgets, whole dumps of `facet_identity` (through `identity_dump`, which survives removals but not additions, `config/retired.py:119-128`) and `graph_nomination` (`content/synthesis/graph_nomination.py:484`). **Under-invalidates:** append's `revision_diff` (`content/synthesis/source_append.py:274-289` omits it), the structuring prompt version, inventory content (only labels, §3.1), model settings beyond provider and model. **Always null:** `asset_hashes`, `extractor_versions`, `lock_fingerprint`. A hit returns the old proposal; an append hit never applies it (`content/synthesis/source_append.py:322-327`). | arc C's incident: removing one unread field moved the key, so finished runs weren't reused (`b77257f189`); for append, the curriculum snapshot changes after every applied append, so append reuse rarely hits anyway |

**Other spend-relevant gaps found on the way:** the structuring pass, persona fire calls and epigraphs are uncheckpointed (§3.4); the persona gate's provider failure is silent (KD5); arXiv imports read the abstract page only (KD3).

## 8. The vault notes for these packages

Input to the strategy; no note was written. Paths are under `docs/learnloop-architecture-vault/`.

### 8.1 Notes checked against the code

| note | claim | verdict |
|---|---|---|
| `Architecture/Content Pipeline.md` | the job ladder (`:34-39`), one vault-writing worker with a parallel DB-only lane (`:60`), `waiting_for_input` holds no lease (`:61`), `auto` prefers GLM-OCR (`:69`), one native-media readiness judgement (`:71`), frozen legacy aliases (`:75`) | **true, and incomplete:** nothing on Add, the automatic build, keep-ahead, cost pause or Undo |
| `Workflows/Import Canonical Sources.md` | heartbeat 15 s, TTL 120 s, `recover_stale_leases` (`:183-184`); ownership guard (`:179`) | true |
| same | checkpoint keys "cover the rendered prompt ... but not the output budget" (`:189`) | **partly stale:** true of inventory windows; synthesis passes key on the prompt **label** (`content/synthesis/source_set_synthesis.py:3035-3075`); the facet judge's key includes the output budget (§3.4) |
| `Workflows/Build a Study Map.md` | the example uses `--ai-provider codex` (`:55`) | **stale:** ADR-018 retired the Codex transport |
| same | `--mode auto` picks bootstrap "when no study map/facets have been applied"; append "limits regeneration to the affected neighborhood" (`:60`) | **partly false:** the rule is "any LO carries the subject" (`content/synthesis/source_append.py:97`), and the append's new inventories are unbounded (KX1); only the neighbourhood is limited |
| `Concepts/Source Authority and Provenance.md` | roles "primary, reference, adjunct, exam-like" (`:50`) | **partly stale:** no `adjunct` role (`content/sources/role_authority.py:25-37`) |
| same | "reviewed application control[s] canonical mutation" (`:58`) | **partly true:** automatic builds apply without review by default (`config/schema.py:911`), and append auto-applies provenance links |
| `Maps/LearnLoop Pipeline Map.md` (reviewed Nov 11) | GLM-OCR first, Marker then pypdf (`:162`); the map version and `responses_to_ir` (`:163`); re-read uses the stored original (`:164`); one alias authority (`:165`); facet meaning through `check_meaning_write` (`:167`) | true |
| `Workflows/Doctor Migrations and Recovery.md` | `--fix-state` "resumes recoverable apply intents" (`:108`) | **true, and the only recovery** (KD2); no note says the sidecar doesn't |
| `Architecture/Privacy and Trust Boundaries.md` | GLM-OCR, native and Marker egress (`:63-68`) | true (the Nov 8 map's §8.1 privacy finding is fixed in this note) |
| `Decisions/ADR-013` | one authority per media modality | true |
| `Examples/Deliberate Canonical Import Session.md` | job phase `extracted` (`:83`) | true |

### 8.2 Features with no explanatory note

- the automatic build: Add, the planner, consent once, cost pause and the daily cap, the book's status line, one-tap Undo (`content/pipeline/add_source.py`);
- keep-ahead reading builds and the reading sweep (`content/pipeline/add_source.py:1761-2043`, `content/pipeline/jobs.py:3971`);
- unit inventory beyond one line, and the append neighbourhood (`content/synthesis/source_unit_inventory.py`, `append_neighborhood.py`);
- the synthesis manifest's three jobs and what it hashes (`content/synthesis/synthesis_manifests.py`);
- facet identity: the judge, groups, merges, aliases, undo (`content/facet_identity/`); only the meaning chokepoint is mentioned;
- write-ahead apply and its recovery (`content/proposals/apply_protocol.py`);
- GLM-OCR's paid-window checkpoints;
- span aliases beyond one bullet;
- the lease mechanisms other than the ingest drain (§3.3);
- the desktop's build-plan, outline and repair flow with its budget overrides.

The generated `Reference/Modules` notes exist for every module in scope (e.g. `Reference/Modules/learnloop/content/pipeline/jobs.md`, `.../content/facet_identity/judge.md`, `.../ingest/extractors/glm_ocr.md`); they're generated and were not judged here.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KV1 | medium | **The journey the learner now uses most (Add → automatic build → keep-ahead) has no note,** nor do facet identity and write-ahead apply. | §8.2 |
| KV2 | medium | **Three notes state rules the code doesn't follow:** checkpoint keys, the bootstrap-or-append rule and "append limits regeneration", and reviewed application. | §8.1 |
| KV3 | low | One stale example (`--ai-provider codex`) and one stale role (`adjunct`). | §8.1 |

## Not verified

- **Nothing was run** beyond AST and import sweeps and read-only queries on backup copies. KX1-KX5 and every crash window are code-traced; each needs its failing test first (the ingestion review's list stands).
- **Spend for KX1 is projected,** not observed: keep-ahead never ran on the copied vaults, and the copies hold excerpts, not whole textbooks. The ratio uses `inventory_json` length / 4 as the token count and the 40,000-token planner cap with block text as the source size; `outline_chapters`' grouping wasn't reproduced.
- **No receipt-based spend exists for synthesis purposes** in the copies (§7); the July token counts come from `agent_runs` and job usage estimates.
- The delegated sweeps' claims were spot-checked at: apply recovery and `pre_hash` (`content/proposals/apply_protocol.py:237-243`, `:342`, `:576`; `ops/doctor.py:1309-1345`), the heartbeat copies (`content/authoring/source_exercise_import.py:781-806` against `source_retrieval/reading_paths.py:819-841`), the arXiv fetch (`content/pipeline/jobs.py:110`), the inventory upsert and reuse (`db/repositories.py:20540-20640`), `holds_claim`'s optional `now` (`db/stores/judgment_claims.py:84-100`), the frontend's retry rule and assessment roles (`IngestActivity.tsx:351-355`, `OutlineAndPlan.tsx:38`), the import-done test (`IngestActivity.tsx:98`), `BUDGET_BOUNDS`, and three vault notes. the B1/B2 call sites without `now` (`content/authoring/source_exercise_import.py:820`, `:838`; `source_retrieval/reading_paths.py:919`), and the job-host line numbers in §2.1-2.2 and §3.3 (about 60 sampled; agent-supplied lines that were off by a few were corrected). **Not spot-checked:** lease rows C-E beyond their definitions and their clocks, the facet judge's group-order capping (`content/facet_identity/judge.py:756-759`), W6's recalibration gap, `reject_applied_items`' per-kind behaviour, the frontend tables' line numbers in §6 beyond `IngestScreen.tsx:716-723`, the polling intervals, and the conflict-resolution crash window the facet sweep inferred (not used above).
- **Corrected from a sweep:** it inferred that GLM-OCR's receipts aren't persisted on the import path; every job's model calls are recorded by the runner (`content/pipeline/runner.py:1031`), so they are.
- `_normalize`'s determinism was read, not tested; whether untitled entities' ULID ids reach any hash wasn't checked.
- `source_retrieval`'s ingest-side consumers were mapped at the import boundary (§3.1) only; their own leases and identities are K6's.
- Desktop polling reloads the vault on some list calls (`learnloop_sidecar/handlers/ingest.py:380-405`, `:530`); the cost wasn't measured.
- Line numbers were machine-checked to exist in their files at `565aee8724`; the text at each was read for the claims in §2.5-2.6, §2.8, §3.4 and §7, and sampled elsewhere.

## Appendix A: every module in scope, classified

The Nov 8 map's class heuristic (§1); `~.` is `learnloop.`. Fan-in and fan-out count imports inside the scope only. `s:helper?` marks a one-importer module of at most 80 code lines.

| module | raw | code | public | funcs | longest fn | in-area fan-in | fan-out | class |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ~.content.authoring | 1 | 0 | 0 | 0 | 0 | 1 | 0 | init |
| ~.content.authoring.ai_contracts | 454 | 361 | 12 | 4 | 6 | 3 | 1 | medium |
| ~.content.authoring.animation_media | 210 | 153 | 5 | 8 | 73 | 1 | 0 | medium |
| ~.content.authoring.authoring_gates | 417 | 262 | 5 | 9 | 71 | 6 | 2 | deep |
| ~.content.authoring.concept_animation | 1550 | 1128 | 29 | 51 | 217 | 2 | 2 | medium |
| ~.content.authoring.conjunctive_items | 321 | 115 | 7 | 9 | 36 | 0 | 0 | medium |
| ~.content.authoring.contract_commissioning | 523 | 306 | 7 | 21 | 79 | 1 | 0 | deep |
| ~.content.authoring.draft_validation | 113 | 68 | 2 | 5 | 50 | 1 | 0 | s:helper? |
| ~.content.authoring.exercise_authoring | 955 | 672 | 8 | 22 | 401 | 1 | 7 | deep |
| ~.content.authoring.item_authoring | 453 | 335 | 6 | 10 | 72 | 0 | 0 | deep |
| ~.content.authoring.laddered_stems | 391 | 189 | 7 | 9 | 138 | 0 | 0 | medium |
| ~.content.authoring.persona_gate | 1629 | 933 | 21 | 43 | 114 | 2 | 1 | deep |
| ~.content.authoring.persona_realism | 319 | 264 | 5 | 11 | 98 | 1 | 0 | deep |
| ~.content.authoring.pf_contracts | 443 | 344 | 29 | 14 | 26 | 0 | 1 | wide |
| ~.content.authoring.pf_sandbox | 420 | 330 | 10 | 12 | 55 | 2 | 1 | deep |
| ~.content.authoring.practice_generation | 2435 | 1779 | 18 | 64 | 206 | 2 | 7 | deep |
| ~.content.authoring.practice_leakage | 483 | 289 | 15 | 25 | 77 | 2 | 3 | medium |
| ~.content.authoring.rung_variants | 891 | 706 | 6 | 14 | 231 | 1 | 3 | deep |
| ~.content.authoring.source_exercise_import | 1718 | 1250 | 25 | 58 | 241 | 2 | 6 | deep |
| ~.content.facet_identity | 11 | 0 | 0 | 0 | 0 | 4 | 0 | init |
| ~.content.facet_identity.actions | 2100 | 1373 | 36 | 70 | 150 | 9 | 3 | wide |
| ~.content.facet_identity.authority | 1405 | 841 | 33 | 61 | 128 | 1 | 9 | wide |
| ~.content.facet_identity.dedupe | 247 | 207 | 3 | 4 | 128 | 0 | 5 | medium |
| ~.content.facet_identity.grouping | 307 | 223 | 5 | 9 | 84 | 2 | 1 | medium |
| ~.content.facet_identity.judge | 1264 | 963 | 28 | 49 | 120 | 5 | 0 | medium |
| ~.content.facet_identity.plan | 468 | 373 | 5 | 14 | 146 | 2 | 5 | deep |
| ~.content.facet_identity.span_support | 137 | 73 | 3 | 3 | 41 | 1 | 1 | s:helper? |
| ~.content.facet_identity.views | 194 | 135 | 3 | 9 | 51 | 4 | 0 | medium |
| ~.content.pipeline | 1 | 0 | 0 | 0 | 0 | 5 | 0 | init |
| ~.content.pipeline.acquisition_preview | 271 | 213 | 3 | 11 | 64 | 2 | 5 | medium |
| ~.content.pipeline.add_source | 2768 | 1859 | 70 | 118 | 159 | 6 | 13 | wide |
| ~.content.pipeline.ai_contracts | 88 | 68 | 4 | 1 | 18 | 1 | 1 | s:helper? |
| ~.content.pipeline.build_plan | 375 | 291 | 6 | 20 | 82 | 3 | 1 | deep |
| ~.content.pipeline.exam_marking | 394 | 242 | 9 | 12 | 64 | 0 | 3 | medium |
| ~.content.pipeline.jobs | 5852 | 4138 | 43 | 209 | 237 | 2 | 29 | deep |
| ~.content.pipeline.quick_add | 490 | 369 | 6 | 14 | 118 | 2 | 5 | deep |
| ~.content.pipeline.reread | 660 | 433 | 21 | 27 | 67 | 2 | 8 | medium |
| ~.content.pipeline.revision_refresh | 230 | 164 | 2 | 6 | 67 | 1 | 5 | medium |
| ~.content.pipeline.runner | 1261 | 870 | 10 | 62 | 148 | 3 | 2 | deep |
| ~.content.pipeline.source_ingestion | 2217 | 1917 | 27 | 90 | 305 | 1 | 10 | deep |
| ~.content.proposals | 1 | 0 | 0 | 0 | 0 | 0 | 0 | init |
| ~.content.proposals.ai_contracts | 911 | 674 | 30 | 12 | 26 | 5 | 0 | wide |
| ~.content.proposals.apply_protocol | 597 | 435 | 6 | 17 | 118 | 3 | 3 | deep |
| ~.content.proposals.conflict_resolution | 89 | 57 | 3 | 2 | 50 | 1 | 0 | s:helper? |
| ~.content.proposals.method_phrasing | 1231 | 829 | 26 | 45 | 127 | 1 | 1 | medium |
| ~.content.proposals.method_statement_judge | 501 | 344 | 16 | 19 | 71 | 3 | 1 | medium |
| ~.content.proposals.patches | 1334 | 1038 | 7 | 38 | 106 | 8 | 4 | deep |
| ~.content.proposals.proposals | 2488 | 1976 | 27 | 83 | 121 | 6 | 4 | deep |
| ~.content.proposals.required_method_override | 273 | 194 | 6 | 7 | 59 | 2 | 2 | medium |
| ~.content.sources | 1 | 0 | 0 | 0 | 0 | 6 | 0 | init |
| ~.content.sources.block_health | 146 | 99 | 2 | 4 | 69 | 0 | 1 | medium |
| ~.content.sources.exam_material | 1588 | 943 | 36 | 80 | 83 | 9 | 3 | wide |
| ~.content.sources.exercise_statements | 204 | 119 | 7 | 7 | 46 | 2 | 1 | medium |
| ~.content.sources.extraction_health | 196 | 137 | 3 | 11 | 33 | 1 | 1 | medium |
| ~.content.sources.front_matter | 30 | 14 | 1 | 1 | 8 | 1 | 0 | s:thin |
| ~.content.sources.math_text | 357 | 243 | 5 | 12 | 50 | 1 | 0 | medium |
| ~.content.sources.pdf_extraction | 273 | 181 | 3 | 11 | 31 | 1 | 4 | medium |
| ~.content.sources.provenance | 122 | 89 | 1 | 2 | 83 | 0 | 0 | medium |
| ~.content.sources.role_authority | 262 | 143 | 8 | 8 | 46 | 9 | 0 | medium |
| ~.content.sources.source_deletion | 336 | 239 | 6 | 12 | 74 | 1 | 0 | medium |
| ~.content.sources.source_library | 144 | 92 | 2 | 2 | 104 | 2 | 2 | medium |
| ~.content.sources.source_outcome_analytics | 279 | 215 | 4 | 6 | 152 | 0 | 0 | medium |
| ~.content.sources.source_outline | 292 | 198 | 9 | 13 | 58 | 10 | 4 | medium |
| ~.content.sources.source_refs | 242 | 188 | 3 | 12 | 79 | 0 | 0 | medium |
| ~.content.sources.span_aliases | 468 | 270 | 18 | 32 | 31 | 1 | 3 | medium |
| ~.content.synthesis | 1 | 0 | 0 | 0 | 0 | 0 | 0 | init |
| ~.content.synthesis.ai_contracts | 1061 | 791 | 51 | 9 | 18 | 4 | 0 | wide |
| ~.content.synthesis.append_neighborhood | 542 | 406 | 4 | 16 | 147 | 1 | 1 | deep |
| ~.content.synthesis.brief | 140 | 81 | 3 | 4 | 29 | 3 | 0 | medium |
| ~.content.synthesis.coverage_rollup | 59 | 44 | 1 | 1 | 49 | 1 | 0 | s:thin |
| ~.content.synthesis.exam_profile | 187 | 129 | 5 | 5 | 87 | 2 | 0 | medium |
| ~.content.synthesis.facet_candidates | 188 | 128 | 3 | 9 | 55 | 0 | 1 | medium |
| ~.content.synthesis.facet_doctor | 121 | 74 | 3 | 6 | 33 | 1 | 1 | s:helper? |
| ~.content.synthesis.facet_mint_gate | 550 | 306 | 11 | 22 | 76 | 2 | 1 | medium |
| ~.content.synthesis.graph_nomination | 1070 | 799 | 13 | 52 | 120 | 7 | 1 | deep |
| ~.content.synthesis.source_append | 1070 | 788 | 5 | 22 | 312 | 3 | 15 | deep |
| ~.content.synthesis.source_coverage | 273 | 217 | 1 | 5 | 145 | 1 | 5 | medium |
| ~.content.synthesis.source_set_synthesis | 3811 | 2971 | 11 | 86 | 1081 | 3 | 20 | deep |
| ~.content.synthesis.source_unit_inventory | 925 | 691 | 18 | 28 | 167 | 4 | 5 | medium |
| ~.content.synthesis.source_unit_selection | 508 | 358 | 11 | 16 | 126 | 8 | 4 | medium |
| ~.content.synthesis.study_map_diff | 79 | 55 | 1 | 2 | 40 | 1 | 0 | s:helper? |
| ~.content.synthesis.synthesis_eval | 302 | 228 | 5 | 10 | 119 | 0 | 0 | medium |
| ~.content.synthesis.synthesis_gates | 1044 | 785 | 7 | 43 | 84 | 7 | 1 | deep |
| ~.content.synthesis.synthesis_manifests | 213 | 138 | 8 | 9 | 56 | 2 | 0 | medium |
| ~.content.synthesis.vault_epigraphs | 361 | 277 | 6 | 14 | 79 | 2 | 1 | deep |
| ~.ingest | 32 | 21 | 0 | 0 | 0 | 0 | 3 | init |
| ~.ingest.block_roles | 378 | 237 | 9 | 8 | 33 | 5 | 0 | medium |
| ~.ingest.detect | 13 | 4 | 1 | 1 | 8 | 1 | 1 | s:thin |
| ~.ingest.extractors | 211 | 150 | 6 | 4 | 60 | 4 | 6 | medium |
| ~.ingest.extractors.base | 170 | 117 | 4 | 6 | 93 | 6 | 2 | medium |
| ~.ingest.extractors.datalab | 205 | 159 | 3 | 11 | 44 | 1 | 3 | medium |
| ~.ingest.extractors.glm_ocr | 1525 | 1099 | 11 | 62 | 136 | 6 | 6 | deep |
| ~.ingest.extractors.glm_text_layer | 682 | 449 | 13 | 27 | 72 | 1 | 0 | medium |
| ~.ingest.extractors.marker | 407 | 280 | 5 | 19 | 80 | 3 | 4 | deep |
| ~.ingest.extractors.marker_worker | 483 | 311 | 2 | 20 | 56 | 2 | 2 | deep |
| ~.ingest.extractors.normalizers | 412 | 326 | 3 | 8 | 110 | 1 | 3 | deep |
| ~.ingest.extractors.pypdf | 192 | 135 | 3 | 7 | 80 | 4 | 3 | medium |
| ~.ingest.fetchers | 400 | 308 | 13 | 19 | 50 | 2 | 2 | medium |
| ~.ingest.hashing | 175 | 108 | 5 | 10 | 29 | 9 | 1 | medium |
| ~.ingest.ir | 396 | 247 | 12 | 16 | 55 | 16 | 0 | medium |
| ~.ingest.locators | 69 | 30 | 3 | 3 | 20 | 6 | 0 | s:thin |
| ~.ingest.models | 79 | 52 | 6 | 2 | 15 | 7 | 0 | medium |
| ~.ingest.originals | 110 | 58 | 6 | 7 | 25 | 3 | 1 | medium |
| ~.ingest.reanchor | 238 | 176 | 5 | 8 | 38 | 4 | 1 | medium |
| ~.ingest.resolution | 80 | 60 | 3 | 2 | 46 | 7 | 1 | medium |
| ~.ingest.transcription | 132 | 96 | 4 | 4 | 66 | 1 | 1 | medium |
| ~.ingest.transcripts | 121 | 75 | 3 | 4 | 36 | 2 | 0 | medium |
| learnloop_sidecar.handlers.facet_detail | 333 | 228 | 5 | 10 | 87 | 0 | 1 | medium |
| learnloop_sidecar.handlers.facet_identity | 86 | 54 | 6 | 3 | 22 | 0 | 1 | s:helper? |
| learnloop_sidecar.handlers.facets | 171 | 108 | 1 | 4 | 141 | 0 | 0 | medium |
| learnloop_sidecar.handlers.ingest | 1608 | 1161 | 75 | 56 | 108 | 0 | 21 | wide |
| learnloop_sidecar.handlers.library | 216 | 154 | 7 | 8 | 47 | 0 | 1 | medium |
| learnloop_sidecar.handlers.library_ask | 832 | 508 | 19 | 40 | 90 | 1 | 2 | medium |
| learnloop_sidecar.handlers.library_exercises | 510 | 306 | 12 | 18 | 78 | 0 | 3 | medium |
| learnloop_sidecar.handlers.proposals | 328 | 225 | 11 | 15 | 50 | 0 | 3 | medium |
| learnloop_sidecar.handlers.source_service | 311 | 214 | 18 | 9 | 37 | 0 | 0 | medium |
| learnloop_sidecar.source_identity | 56 | 35 | 1 | 1 | 41 | 1 | 0 | s:thin |
