# Refactor A4: correct what's dangerous now

Step A4 of `docs/specs/refactor_strategy_v3.md` (§2.3). Docs only; no `src` change. Base: main `cf45777002` on `refactor/map`, Nov 9.

## The privacy claim, checked against the code

Three notes said PDF extraction is local (Marker or pypdf) unless `engine = "native"`. The code at this tip:

| Where | What it does |
|---|---|
| `src/learnloop/ingest/extractors/__init__.py:84` `pdf_extractor_for` | `engine = "auto"` (the default, `config/schema.py` `PdfIngestConfig.engine`) asks `selected_backend` first and returns `GlmOcrDocumentExtractor` when it names one; only then Datalab (if `LEARNLOOP_MARKER_PROVIDER=datalab`), local Marker, pypdf |
| `src/learnloop/ingest/extractors/glm_ocr.py:185` `selected_backend` | `backend = "auto"` (the default) or `"api"` returns `"api"`, z.ai's hosted `layout_parsing` (`API_URL`), whenever a key is in the environment: `api_key_env` (default `ZAI_API_KEY`), `ZHIPU_API_KEY`, `ZHIPUAI_API_KEY`. `"local"` returns a self-hosted server that answers, whose `local_url` may be another computer. `local_only` refuses z.ai and non-loopback servers |
| `glm_ocr.py:312` | A hosted run without `whole_file_upload_allowed` raises `GlmOcrConsentRequired` |
| `src/learnloop/content/pipeline/jobs.py:261` `_document_extractor` | The durable import: under `auto`, with no `glm_ocr_upload` consent and no OK card, a PDF is read by `local_pdf_extractor` (local Marker or pypdf, never hosted Marker) and flagged `glm_ocr_needs_upload_ok`; otherwise `_guard_file_upload(ctx, "glm_ocr_upload", ...)` waits for the learner's OK. An image asks for the OK. A repair the learner OK'd as local never leaves the computer |
| `src/learnloop/content/sources/pdf_extraction.py:122` `_resolve_engine` | The one-shot `learnloop ingest` path: hosted GLM-OCR only with `whole_file_upload_allowed` (the vault's `glm_ocr_upload` consent, `source_ingestion.py:2136`) |

**Verdict:** the map's §8.1 row holds. With a z.ai key set, `auto` sends the whole file to z.ai, gated by a one-time OK naming z.ai; without the OK it reads locally. The notes said "local" with no qualification, which was wrong. Datalab, which the notes also didn't mention, is opt-in by environment variable.

## What changed

| File | Change |
|---|---|
| `Architecture/Privacy and Trust Boundaries.md` | "Source acquisition egress": the PDF sentence now states GLM-OCR first under `auto`, z.ai with a key after the OK, a self-hosted server possibly elsewhere, the local-only repair, Datalab, then native |
| `Architecture/Content Pipeline.md` | "Extraction choices": the same order in one sentence, with links to the two notes that hold the detail |
| `Workflows/Import Canonical Sources.md` | "Choose the PDF engine": `auto` row corrected, `glm_ocr` row added, `marker` and `pypdf` split, a paragraph on keys, the OK, Datalab and local repairs |
| `Maps/Developer Map.md` | The scheduler-first row ("next-item policy lives in `scheduling/`", map §8.3) replaced by the plan engine and router; a new "Where to change what" table: §6's sample changes, where each lives today and the plumbing it costs today. Each refactor step that moves one updates its row |
| `CLAUDE.md` | "5 hard-coded paths" for the head fixture was 71 files (68 tests and 3 scripts, map Appendix A row 2), now given as a scoped `git grep`; "~450 test files" was 1,385. The suite time (N2) was already fixed by the test-suite branch |
| `README.md` (separate commit) | It repeated the claim: "Marker is enabled when engine is explicitly `marker`" and "`npm run dev` keeps local Marker/pypdf". Corrected, with a short paragraph on when PDFs leave the computer. Also stale: the desktop timeout (240 s; `sidecar.rs:14` is 16 × 60 = 960 s) and "full suite (~17 minutes)" (now `-n 8 --dist worksteal`, about 15 minutes, `docs/reviews/test-suite-audit.md` §8) |

The notes' `source_commit` and `last_reviewed` stamps are unchanged: only the named passages were re-read, not the whole notes. The large rewrite is still last (§5).

## Checked and left

- `LearnLoop Pipeline Map.md:148` already says "GLM-OCR, else Marker, else pypdf". Consistent now.
- CLAUDE.md's "~40 phone-host tests skip silently" without `--extra mobile`: not re-counted.
- `validate_vault.py` passes after the edits (2,250 notes).

## Not done here

- The rest of the map's §8.1 and §8.3 rows (deterministic-controller claims, table counts, migration heads): the last stage's job (§5).
- The README edit touches a file the owner has uncommitted local edits to in the main checkout (its first line). It's its own commit so the landing can take it separately.
