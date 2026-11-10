# Refactor A4: correct what's dangerous now

Step A4 of `docs/specs/refactor_strategy_v3.md` (§2.3). Docs only; no `src` or test change. Two passes:

- **First pass** (`4d7b49f62f`, README in `c01720ef1f`), on `refactor/map` at main `cf45777002`, Nov 9, before the strategy's step order. It landed on main with the map. It fixed the three notes' "PDFs are local" claim, the README's copy of it, the Developer Map's scheduler-first row, and CLAUDE.md's head-fixture path count.
- **This pass**, on `refactor/a4-dangerous-docs` from A2's tip `7e7d68c123`, merged into A3 for one gate. It rechecked the privacy claim against the code at this tip and fixed what the first pass left imprecise. It put S0's measured suite times in CLAUDE.md and rebuilt the Developer Map's "where to change what" table in the form §6 asks for: what to edit, the test or golden that shows it, the note to update.

## The privacy claim, checked against the code (this tip)

The question: when does a PDF, or its text, leave the computer?

| Claim | Evidence |
|---|---|
| `auto` is the default engine | `src/learnloop/config/schema.py:719` (`PdfIngestConfig.engine`) |
| `auto` and `glm_ocr` ask GLM-OCR first; `pypdf` is always local; `native` is refused by the local registry | `src/learnloop/ingest/extractors/__init__.py:84` (`pdf_extractor_for`), `:112` |
| GLM-OCR's `backend = "auto"` (the default) or `"api"` means z.ai whenever a key is set, and nothing otherwise. A self-hosted server is used only with `backend = "local"`, when it answers. `local_only` refuses z.ai and any non-loopback server | `src/learnloop/ingest/extractors/glm_ocr.py:185` (`selected_backend`), `schema.py:696` |
| The key comes from `api_key_env` (default `ZAI_API_KEY`), then `ZHIPU_API_KEY`, `ZHIPUAI_API_KEY`. They're read from the environment the app loaded: shell, vault `.env`, machine `settings.env` | `glm_ocr.py:122`, `:138` (`glm_api_key`) |
| z.ai gets the whole file at `https://api.z.ai/api/paas/v4/layout_parsing` | `glm_ocr.py:7-10` (module docstring), `:94` |
| A hosted run without `whole_file_upload_allowed` raises `GlmOcrConsentRequired` | `glm_ocr.py:312` |
| Hosted counts as leaving the computer, and so does a self-hosted server off loopback | `glm_ocr.py:305` (`leaves_this_computer`) |
| Durable import, under `auto` with z.ai selected and no z.ai OK: a plain import reads the PDF with `local_pdf_extractor` (local Marker or pypdf) and flags it `glm_ocr_needs_upload_ok`. An image or an Add (`require_upload_ok`) goes to `_guard_file_upload(ctx, "glm_ocr_upload")`, which waits for the OK | `src/learnloop/content/pipeline/jobs.py:261` (`_document_extractor`), `:299-312`, `:425` |
| A scan read locally only for lack of the OK asks for the OK on its card | `jobs.py:508-521` |
| The z.ai OK is its own record, `whole_files_zai`. Other whole-file uploads use `whole_files`. Both live in `[ai.consent]` | `src/learnloop/content/pipeline/add_source.py:78`, `:83`, `:529`, `:535` |
| Only z.ai's upload asks without `require_upload_ok`. Datalab (`pdf_upload`), native (`pdf_upload`) and audio transcription ask only on an Add | `jobs.py:425` (`_guard_file_upload`), `:481`, `:489`, `:493` |
| A self-hosted GLM-OCR server is never guarded by an OK: the guard runs only for `extractor.backend == "api"` | `jobs.py:299` |
| Datalab: `LEARNLOOP_MARKER_PROVIDER=datalab` with `DATALAB_API_KEY` sends the PDF to `https://www.datalab.to/api/v1/convert` wherever Marker would run (`auto` reaches it only after GLM-OCR is passed over) | `__init__.py:125`, `src/learnloop/ingest/extractors/datalab.py:22-23`, `jobs.py:226` |
| A local repair: `native` becomes `auto`, Datalab becomes `pypdf`, and z.ai and remote servers are passed over | `jobs.py:174-185`, `:187`, `:292-298` |
| Marker's `use_llm` sends difficult regions to an OpenAI-compatible endpoint. The durable path sets it only for a repair whose options ask for it ("external VLM", behind an explicit consent record); the one-shot path reads `[ingest.pdf] use_llm` (default off) | `jobs.py:2861`, `src/learnloop/content/sources/pdf_extraction.py:163`, `schema.py:725` |
| The one-shot `learnloop ingest` path: hosted GLM-OCR only with the vault's `whole_files_zai` OK; otherwise local | `pdf_extraction.py:58`, `:122` (`_resolve_engine`), `src/learnloop/content/pipeline/source_ingestion.py:2136` |
| `native` sends the whole PDF to the `canonical_ingest` chat provider. The Ingest screen says so beside the choice | `schema.py:715-719`, `apps/learnloop-tauri/src/screens/IngestScreen.tsx:1185` |
| Extracted text, as passages, goes to the connected AI under the connection's OK (`passages_and_answers`) | `add_source.py:76` (`DATA_FLOW`), `:536-539` |

**Verdict.** The map's §8.1 row holds, and the first pass's notes were mostly right. This pass corrects four imprecisions:

1. The notes said `auto` uses "a self-hosted server that answers". It uses one only with `backend = "local"`.
2. Nothing said a self-hosted server gets the pages with no OK, even when it runs on another computer.
3. Privacy said both native paths "are named on the acquisition consent card before any bytes leave the machine". Only an Add asks for the separate `whole_files` OK. A plain import whose engine was chosen explicitly asks nothing more; the Ingest screen states it beside the choice.
4. Privacy said `auto` reads locally until the OK is given. That holds for a plain import. An Add, an image and a scan wait for the OK on the book's card instead.

Marker's `use_llm` and the text-passage flow weren't mentioned; they are now.

**Not a bug, but worth the owner's eye.** A `backend = "local"` GLM-OCR server whose `local_url` is on another computer gets page images with no OK. That's an explicit configuration choice, and `leaves_this_computer` is consulted only for local repairs (`jobs.py:292`). It's documented now, not changed.

## What changed in this pass

| File | Change |
|---|---|
| `Architecture/Privacy and Trust Boundaries.md` | "Source acquisition egress": the PDF paragraph is now a list, one item per way out: z.ai, a self-hosted server, neither, Datalab, native, Marker's `use_llm`. Then a paragraph on which OK covers what, local repairs, and extracted passages |
| `Architecture/Content Pipeline.md` | "Extraction choices": a self-hosted server needs `backend = "local"`, and it asks no OK. "Reading locally meanwhile" is now limited to a plain import |
| `Workflows/Import Canonical Sources.md` | "Choose the PDF engine": the `auto` row names `backend = "local"`; the `marker` row names Datalab. The paragraph below now covers the scan, image and Add cases, says the z.ai OK covers only z.ai and that Datalab and native uploads on an Add need the whole-file OK, says self-hosted servers ask no OK, and lists what a local repair passes over. It links to Privacy for the full list |
| `Maps/Developer Map.md` | "Where to change what" rebuilt as Change / Edit / The test or golden that shows it / Note to update, 14 rows (§6's sample changes plus the speed-work row). S0's corrections are kept: the objective is `_Ledger.q`, and `_terms` only reports. So is A2's head-fixture row. A closing line records the 48 digests that A3 replaced |
| `CLAUDE.md` | Commands: full suite "about 2 h serial", `-n 8 --dist worksteal` "about 19 min, 10 GB", durability "about 7 min serial"; times now point at `docs/reviews/refactor-baseline.md` (S0: 1,119.8 s, 435.8 s, 7,273.4 s). Tests: "from 59 to 15 minutes" is now "from 59 minutes to under 20 at `-n 8`". Nothing else in CLAUDE.md changed |

`README.md` is unchanged in this pass. Its privacy paragraph (lines 224-230, from the first pass) is still accurate: "with a self-hosted GLM-OCR server configured", and marker/pypdf keep extraction local "and leave out the hosted Datalab route". The notes' `source_commit` and `last_reviewed` stamps are unchanged, because only the named passages were re-read. The large rewrite is still last (§5).

## Depends on A3 (check at the merge)

- **Developer Map, the default, seed and route rows** name `tests/goldens/effective_defaults.toml` and "the golden test's write command". That file doesn't exist at this tip. A3 creates it, and these rows describe the state after A3. If A3 names the file, its test or its write command differently, change those three rows and the tag row ("the golden line of its kill switch").
- **Developer Map, the closing line** says A3 replaced the 48 frozen digests (one per tag through mvp-0.57, `DEFAULTS_SNAPSHOT_BY_ALGORITHM` in `config/template.py`). It's true only once A3 has landed.
- **Not A4's to fix:** `Architecture/Testing and Invariants.md:72` says a new version needs a "defaults fingerprint". `Concepts/Algorithm Versions and Reproducibility.md` and `docs/algorithm-change-playbook.md` step 4 probably say the same. A3 makes these false, and they're on its list (playbook step 4, Algorithm Versions). Testing and Invariants isn't on its list.

## Checked and left

- `README.md:567`: "full suite (about 15 minutes; times in docs/reviews/test-suite-audit.md)" is stale against S0 (18:40 at `-n 8`). The brief allows README edits only for the privacy correction, so this is left for the owner or a later step.
- `Maps/LearnLoop Pipeline Map.md:148` and `:162`, and `Reference/Configuration/learnloop.toml.md:73` and `:99` (generated): consistent with the code.
- `Reference/Refactor Status.md` is about the August refactor; nothing here makes it false.

## Validator

`validate_vault.py`, run through the isolation wrapper with `uv run --no-project --with ruamel.yaml`: passed. 2,271 notes, 59,050 WikiLinks and fragments, 8,044 source paths, 2,269 of 2,269 reachable from Home.

## Rules

All edits but one were made with the Edit tool. The Developer Map's section was swapped by a short exact-match script, which checked that its section heading occurred exactly once. That script ran with the system `python3` and not under the isolation wrapper. It read and wrote only that note, with no imports beyond `sys`. Nothing else ran Python outside the wrapper. No tests were run, since there was no source or test change.
