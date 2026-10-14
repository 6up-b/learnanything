# GLM-OCR as the main document reader

**Owner request (2026-10-13):** make GLM-OCR the main pipeline for Reader document ingestion, with its **complete** layout-and-recognition pipeline (PP-DocLayout-V3 layout, then parallel recognition by the 0.9B GLM-OCR model) instead of marker-pdf/surya, run either through z.ai's API or locally. Marker and pypdf stay as fallbacks.

**Branch:** `ingest/glm-ocr` (worktree `learnanything-glmocr`), base main `e5f880778`.
**Implementation:** Codex (job `20261013-211638-u7HXDy`, offline, uncommitted), then reviewed, reworked and finished here.
**Commits:** `26e9df091` (pypdf surrogates), `0b480dd85` (extractor, selection, config), `c040c9803` (import, Reader, Settings, legacy path, tests), `70866da16` (desktop), `2ff0863bd` (the scan lines offer Settings), `11707c6bc` (the ingestion spec), `3c2bd2124` (DB/config references and the template note), `7bc0ee921` (the Tauri command), `72d98eb7c` (key-test isolation), and the commit with this record. The session that made the first five crashed before the gate; the restarted session ran the gate, whose two failures the last two commits fix.
**Migration:** none. **Algorithm successor:** none (document extraction only; no scoring, scheduling, projection or serving change). **New config:** `[ingest.pdf.glm_ocr]` and the `glm_ocr` engine. **New sidecar RPC:** `set_text_recognition_api_key` (desktop only). **Paid calls:** none (see the live check).

## What changed

- **`learnloop.ingest.extractors.glm_ocr`** — `GlmOcrDocumentExtractor` for PDF, PNG and JPG, plain stdlib HTTP (no SDK):
  - **api**: z.ai `POST https://api.z.ai/api/paas/v4/layout_parsing` (or Zhipu's `open.bigmodel.cn`), `Authorization: Bearer`, the file as a data URI (or raw base64), crop images and visualisation off, a `request_id`, one-based `start_page_id`/`end_page_id`.
  - **local**: the glmocr SDK's `python -m glmocr.server` (`POST /glmocr/parse`). That server reads PDFs only from its own disk, so LearnLoop renders the selected pages to PNG data URIs (pypdfium2) and sends `{"images": [...]}`.
- **Selection** (`pdf_extractor_for`): `auto` = GLM-OCR when it can run (hosted with a key; local only when `backend = "local"` and the server accepts a TCP connection), then local Marker, then pypdf. The reason goes into extraction health (`glm_ocr_api_selected`, `glm_ocr_unavailable_marker_selected`, `glm_ocr_and_marker_unavailable_pypdf_selected`). Explicit engines fail rather than switch. Only GLM-OCR reads an image.
- **Runtime fallback** (`extract_with_fallback`): under `auto`, a GLM-OCR failure falls back to local Marker, else pypdf (`glm_ocr_failed_<engine>_fallback`; the book card then says "Text recognition didn't work this time, so this is a plainer reading" with "Read it again"). Marker still falls back to pypdf. A missing OK, a spend refusal or a cancellation never falls back; an image never does; two failures keep the `pdf_extraction_failed` error.
- **Consent and privacy**: a hosted run waits for the existing one-time whole-file OK, worded "Reading this document sends the whole file to z.ai (GLM-OCR)", on every import that would use it. A book kept on this computer never goes to z.ai: `auto` reads it locally, an explicit `glm_ocr` engine refuses with `kept_local`, and a local server counts only on a loopback address. Remote links download raw, so nothing is recognised before the OK. No per-book opt-out was added.
- **Spend**: each physical request (each retry too) gets its own `SpendBudget` admission with no per-file money cap (the shared envelopes, such as an automatic build's daily guard, and the metered request gate still apply) and its own `model_call` receipt: provider `zai-glm-ocr` / `glm-ocr-local`, reported input, output and cached tokens, cost at `price_per_million_tokens` (0.03), latency in `usage_json`. Without reported usage the cost is the labelled estimate (`estimated_usage_missing`). Local runs cost 0. The automatic-build pricing reads the same price.
- **Previews**: pages × 6,000 input+output tokens (`ESTIMATED_TOKENS_PER_PAGE`) at the configured price. A link's page count is unknown until it is downloaded. The z.ai upload is named in `potential_external`.
- **Reader / UX**: "Read it again with text recognition" uses GLM-OCR when it can run for the book (hosted needs only the key), else Marker. The how-to copy is now "To add it, paste a z.ai API key in Settings, under Ingestion." Settings → Ingestion has that key field (saved to the machine's `settings.env` like the transcription key). The Ingest screen and Add accept PNG/JPG and show the estimate.
- **Legacy one-shot path** (`extract_pdf_markdown`): uses hosted GLM-OCR only when the vault has the whole-file OK. Without it, `auto` reads locally (`glm_ocr_needs_upload_ok`) and an explicit `glm_ocr` fails asking for the OK. Caches by extractor version.
- **pypdf fix** (found by the fallback comparison below): pypdf returns lone surrogates for some maths-font glyphs, which crashed `block_content_hash`. They now become U+FFFD.
- Config `[ingest.pdf.glm_ocr]`: `backend`, `api_url`, `api_key_env` (`ZAI_API_KEY`, then `ZHIPU_API_KEY`/`ZHIPUAI_API_KEY`), `local_url`, `request_timeout_seconds` (180), `max_pages_per_request` (30), `price_per_million_tokens` (0.03), `base64_style`. These are modelled defaults, so all fourteen defaults snapshots were recomputed. The decision-only template names the engine choice.

## Design notes

**Response shapes.** The pages we had described the hosted `bbox_2d` as normalised 0–1. The glmocr 0.1.5 SDK source (read from its PyPI wheel, not executed) says otherwise. Its MaaS client documents hosted `bbox_2d` as **absolute pixels of z.ai's own page render**, with sizes in the region's `width`/`height` and in `data_info.pages`. Its self-hosted layout detector writes **0–1000** boxes. Its Flask server returns the same value as `json_result` and `layout_details`: `[[regions]]` for one input, one `[[regions]]` per image for several. Region labels are the coarse `text`/`table`/`formula`/`image`. Titles keep `native_label` (`doc_title` → `# `, `paragraph_title` → `## `), formulas come as `$$\n…\n$$` (with `\tag{n}` merged in), and tables as HTML. Headers, footers, page numbers and footnotes are dropped by the default `abandon` mapping. The normaliser handles every one of these shapes, plus the older flat and page-object shapes. A declared `coordinate_system` wins. Otherwise: values ≤ 1 are fractions, a known page pixel size means pixels, and anything else is 0–1000. The shape seen is recorded in health (`glm_ocr_response_nested` / `units` / `flat` / `page_objects`).

**Geometry.** Boxes become PDF points with a top-left origin, in the page's crop box after rotation. That is the space `reader.pdf_view` and the block crop draw in (pdfium's page size). Images keep pixels. IR pages stay zero-based like Marker, pypdf, outlines and repairs. Only API page ids are one-based.

**Mapping.** Titles (`doc_title`/`paragraph_title`, or a one-line `#` heading) become SectionHeader blocks and the section path. Multi-line text is never a heading. Formulas keep or gain `$$`. HTML tables become GFM, because the Reader renders GFM but no raw HTML: spans repeat, pipes are escaped, a stray `<` in LaTeX stays text. Image regions are Figure blocks with no text: crop URLs and Markdown image references are never fetched or kept. `figure_title` becomes a Caption block and algorithm regions become Code. Units come from the PDF outline when it has two or more entries (Marker's rule). Otherwise they come from detected headings, split by block so several headings can share a page. An incomplete or unreadable layout fails rather than reading as empty.

**Requests.** A document that fits one window (≤ 30 pages, ≤ 50 MB) goes as it is, with its page range. Otherwise each window of at most 30 contiguous selected pages goes as its own PDF (pypdf), halved while over 50 MB, so a long book is not uploaded whole once per window. 429/5xx retry twice (Retry-After capped at 30 s, else 1 s then 2 s), sleeping outside the admission. Redirects are refused, so neither the key nor the file follows them. Provider errors keep the provider's code and message, with the key scrubbed.

**Hashes.** The extraction request hash covers the same PDF config as before. `auto` stays implicit, so unchanged sources keep their hashes. The GLM-OCR settings travel beside it: endpoint, timeout, price and window never change what is read. The extractor version `glm-ocr-0.9B+PP-DocLayout-V3+<backend>+map1` and `model_versions` (backend, recognition, layout) move the hash when the backend, models or mapping change. The IR schema and Marker's chunk map are unchanged.

## Review of Codex's draft

Kept: the module layout, the stdlib transport, the consent and spend hooks through `SpendBudget` + `model_call`, the windowing idea, the table-to-GFM conversion, the zero-based IR pages, the receipts, the preview estimate, raw remote downloads, the image category, and the desktop wiring. Fixed or changed:

| # | Problem in the draft | Resolution |
|---|---|---|
| 1 | **A kept-local book was sent to z.ai.** The upload guard skipped the kept-local refusal for `glm_ocr_upload`, and selection ignored `keep_local` (the card also offered hosted recognition for kept-local books). | Selection takes `keep_local`. The guard refuses as for every other upload. `text_recognition_available` and the re-read respect it. Tested. |
| 2 | **Pixel boxes mis-scaled.** A `bbox_2d` with all values ≤ 1000 was read as 0–1000 even when it was in pixels (z.ai's actual format), so one page mixed scales. | Per-response space: page pixel size known means pixels, else 0–1000 (SDK-verified). |
| 3 | **The self-hosted multi-image response crashed.** One `[[regions]]` per image read as malformed. | The "units" shape is flattened. Tested against a real loopback HTTP server. |
| 4 | **Request hashes and Marker options drifted.** `_pdf_payload_config` merged the vault's whole `[ingest.pdf]` (and GLM settings) into the hashed config. That moved every PDF's hash and newly passed `use_llm` etc. to Marker in the durable path. | Restored the hash-stable config. GLM settings travel unhashed. Tested. |
| 5 | **A local server was probed in `auto` by default.** That depended on `exclude_unset`, which the template defeats, so the preview could claim "local, $0" with no server. | `auto` never probes; `local` must be chosen. |
| 6 | **Multi-line text starting `#` became a one-line heading**, dropping the rest. | Only title labels or one-line headings count. |
| 7 | **The caption was copied into the figure *and* kept as a block** (shown twice). | Caption stays its own block. |
| 8 | **The frozen legacy template was edited**, along with an unrequested legacy marker→pypdf fallback and its test. | Reverted. |
| 9 | **The `glm-ocr` extra (`glmocr[selfhosted]`) cannot share an environment with `pdf`** (Pillow ≥ 12 vs marker-pdf < 11). A uv conflict declaration would move the base environment to Pillow 12 and regex 2026. | The extra carries only pypdfium2. The glmocr server runs in its own environment (below). |
| 10 | **Import contracts broke.** The new ingest → ai edge closed an ingest → ai → db → ingest package cycle. | Exempted the three leaf edges with their reason (`ai.execution`/`ai.spend` import only the stdlib and `ai.errors`). |
| 11 | **An image without GLM-OCR fell to pypdf/Marker** and failed confusingly. A PDF-only engine sent an image to the native PDF model. | Clear `pdf_extractor_unavailable` ("Text recognition isn't set up" → Settings); PDF-only engines read images the automatic way. |
| 12 | **Retry backoff slept while holding the request's admission.** Error messages dropped the provider's reason. | Sleep after release; code and message kept, key scrubbed. |
| 13 | **The how-to copy pointed at "machine settings"**, which a learner cannot reach. | A Settings field, plain copy, and "Set it up" on the scan lines. |

Found by the gate after the restart (both in the review's own additions):

| # | Problem | Resolution |
|---|---|---|
| 14 | **The Settings key field called a command the Tauri shell did not forward** (`test_desktop_rpc_contract`): the sidecar method and the TypeScript client existed, `commands.rs`/`main.rs` did not. In the app, saving the key would have failed with "command not found". | `set_text_recognition_api_key` passes through like the transcription key (`7bc0ee921`); `cargo check` clean. |
| 15 | **The key test leaked a key into other xdist workers.** It saved `ZAI_API_KEY` into the session-wide isolated `settings.env`, which every worker shares; a vault load in another worker during that window took the key into its environment for good, and a later PDF test there chose hosted GLM-OCR and stopped at the whole-file OK (`test_native_pdf_fallback_when_unavailable_uses_local_with_health_flag`). | The test uses its own `LEARNLOOP_CONFIG_DIR`, like the other key tests (`72d98eb7c`). |

## Tests

- `tests/test_glm_ocr.py` (42, fakes only): request building (Bearer header, data URI vs raw, page ranges, 30-page windows as their own files, selections, oversize splitting, image limit, https and plain URL, no redirects), retries with separate admissions and receipts and Retry-After, errors without the key, receipts and cost (reported, missing usage, local zero, daily-gate pricing), consent and spend refusals sending nothing, the mapping (reading order, roles, headings, units from headings and outline, a lone bookmark, formulas, tables, figures and captions, point boxes, rotated crop boxes), every response shape (hosted nested, self-hosted units and single, flat, page objects, incomplete), selection and fallbacks with reasons (aliases, keep-local, loopback-only local, refusals never falling back, double failure), versions and hash identity, the local backend against a real loopback HTTP server (PDF pages rendered, image), the durable Add (OK asked naming z.ai, then read, spend recorded), kept-local books never uploading, identity unchanged by endpoint/price/timeout, image imports, the re-read engine, the preview, the legacy path's consent and cache, raw remote downloads, and Settings saving the key.
- `tests/test_pdf_extractor_selection.py`: pypdf surrogates. Updated: `test_ux_phase1_usability_round2.py` (the how-to copy), `test_ux_phase1_add_source.py` (the unsupported line names images), `test_mobile_allowlist.py` (the new RPC pinned desktop only), and the CLI help snapshot.

## Gate

Run on the restarted session (`TMPDIR=fixtures-local/tmp`, `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`), the machine shared with other worktrees' suites.

- `uv run lint-imports --no-cache`: 17 kept, 0 broken.
- Targeted (`test_glm_ocr`, `test_pdf_extractor_selection`, the UX Phase 1 add-source and usability rounds, `test_mobile_allowlist`, `test_mvp021_upgrade` (defaults snapshots), `test_cli_help_snapshot`): 210 passed.
- Full suite, first run (`pytest -n auto`, at `2ff0863bd`): 10648 passed, **2 failed**, both real and fixed (review rows 14 and 15): `test_desktop_rpc_contract::test_every_frontend_call_is_registered_with_tauri` and `test_ingest_runner::test_native_pdf_fallback_when_unavailable_uses_local_with_health_flag` (passes alone; the cross-worker key leak).
- Full suite, rerun after the fixes (`72d98eb7c`): **10650 passed**.
- Durability lane (`pytest -m durability`, at `72d98eb7c`): **99 passed** (10551 deselected).
- Frontend (`apps/learnloop-tauri`): `npm run typecheck` clean, `npm test` 482 passed (73 files), `npm run frontend:build` built. `cargo check` (the shell gained a command): clean.
- References: `db_generate_reference.py` then `db_validate_reference.py` (no errors; 822 configuration leaves, prose counts in `Configuration.md` and `Database.md` updated by hand), `validate_vault.py` passed (1102 notes). The CLI help snapshot and all fourteen defaults snapshots were already regenerated in `0b480dd85`/`c040c9803`.

## Live check: skipped, the app reports no z.ai key

Following the rule, the check ran through LearnLoop's own loading (`load_config` / `load_vault` on a scratch vault in `fixtures-local/glm-live-vault`). That load reads the vault `.env` and the machine settings file `~/.config/learnloop/settings.env` into the environment. Neither `ZAI_API_KEY`, `ZHIPU_API_KEY` nor `ZHIPUAI_API_KEY` was set afterwards. Listing only the names of the variables the machine settings file added (no values) showed two, neither for z.ai. No settings file was read directly and no key was printed. So no hosted request was made and nothing was spent. Rechecked the same way after the session restart (about 22:35): the app's load still adds two variables, none named like z.ai/Zhipu/GLM, and `glm_api_key()` is empty, so the check stays skipped. The z.ai key is most likely in the repository-root `settings.env` (the main checkout's gitignored file), which LearnLoop itself never reads.

**To enable it:** paste the key in Settings → Ingestion → "text recognition key" (new in this change), or add `ZAI_API_KEY=…` to `~/.config/learnloop/settings.env`. Then rerun the check below.

**What was run instead:**

- **Documents** (untrusted, each in its own new directory, read with `python -I` / the app):
  - `fixtures-local/glm-live-arxiv/2302.11517.pdf`: arXiv 2302.11517, "A Global and Patch-wise Contrastive Loss for Accurate Automated Exudate Detection" (CC BY 4.0, checked on the abstract page). 5 pages with display equations and two tables.
  - `fixtures-local/glm-live-scan/byrne_page5.jpg`: Oliver Byrne's *Euclid* (1847), Book I Prop. V, a public-domain scan from Wikimedia Commons via the Internet Archive. 1758×2496 JPEG, 312 KB.
- **Dry run** (the app's acquisition preview, no key): the PDF is configured for `pypdf`, the image for `text_recognition_unavailable`, no estimate and no external upload. With a key, the same preview would estimate 6 pages × 6,000 = 36,000 tokens ≈ **$0.0011** at $0.03/M, far under the $0.50 ceiling.
- **Imports into the scratch vault** (`learnloop import`, no key):
  - The JPEG fails plainly: `pdf_extractor_unavailable`, "Text recognition needs a z.ai API key or a running local GLM-OCR service". The card says "Text recognition isn't set up" and offers "Set it up".
  - The PDF first **failed** with `UnicodeEncodeError`: pypdf's text held lone surrogates. That is a pre-existing pypdf-fallback bug, fixed in `26e9df091`. After the fix it completes with `glm_ocr_and_marker_unavailable_pypdf_selected` in health.
- **pypdf baseline for the GLM-OCR comparison:** 5 blocks (one Text block per page), 0 Equation and 0 Table blocks, 24,049 characters with 16 U+FFFD where maths glyphs were, and 15 units from the PDF outline. Equations (3)–(4) come out as fragments, for example `Lpd = 1\n|M|\nX\nf p\ni ∈M\nL(f p\ni , P(p), N (p)), (3)`. Table 1 comes out as run-on lines, for example `U-Net w/ Proposed52.10(0.21) 66.96(0.25) 95.87 (0.19)61.08(0.60)`. Marker is not installed in this environment (the `pdf` extra), so there is no Marker column.
- **Not measured** (they need the key): the live response shape, pages, blocks by role, a stored formula and table, time per page, tokens and cost.

**Rerun with the key** (about $0.002):

```bash
cd learnanything-glmocr
uv run python - <<'PY'
from pathlib import Path
from learnloop.content.pipeline.add_source import FILE_UPLOAD_CONSENT
from learnloop.ops.settings_store import apply_config_updates
apply_config_updates(Path("fixtures-local/glm-live-vault/learnloop.toml"), {
    ("ai", "consent", FILE_UPLOAD_CONSENT, "granted_at"): "2026-10-13T00:00:00Z",
    ("ai", "consent", FILE_UPLOAD_CONSENT, "data_flow"): "whole_files",
    ("ingest", "pdf", "engine"): "glm_ocr"})
PY
uv run learnloop import --vault fixtures-local/glm-live-vault --json \
  fixtures-local/glm-live-arxiv/2302.11517.pdf fixtures-local/glm-live-scan/byrne_page5.jpg
```

Health then names the response shape (`glm_ocr_response_*`), and receipts hold tokens, cost and latency (`usage_json`). If the shape differs from the SDK's description, add the recorded response as a fixture in `tests/test_glm_ocr.py` and adapt `_page_regions` / `_bbox`.

## Run GLM-OCR locally

These instructions were not executed here (no GPU or model download). Run them in an environment of its own, because glmocr needs Pillow ≥ 12 and transformers ≥ 5 while marker-pdf pins Pillow < 11.

1. Serve the recognition model. vLLM ≥ 0.19: `vllm serve zai-org/GLM-OCR --port 8080 --served-model-name glm-ocr`. SGLang or Ollama also work (`pipeline.ocr_api.api_mode: ollama_generate` for Ollama's `/api/generate`).
2. Install the SDK with its layout model and server: `uv venv ~/glmocr-env && uv pip install --python ~/glmocr-env 'glmocr[selfhosted,server]'`. PP-DocLayoutV3 runs on CPU or CUDA (`pipeline.layout.device`).
3. In a copy of the SDK's `config.yaml`, set **`pipeline.maas.enabled: false`**. The SDK ships with MaaS **on**, which would forward everything to Zhipu's cloud. Point `pipeline.ocr_api.api_host` / `api_port` at the recognition server, and keep `server.port: 5002`.
4. Run `~/glmocr-env/bin/python -m glmocr.server --config config.yaml`.
5. Configure LearnLoop. `uv sync --extra glm-ocr` installs pypdfium2, which renders PDF pages for the server. Then set:

   ```toml
   [ingest.pdf]
   engine = "auto"          # or "glm_ocr" to fail rather than fall back

   [ingest.pdf.glm_ocr]
   backend = "local"
   local_url = "http://127.0.0.1:5002/glmocr/parse"   # loopback, so kept-local books may use it too
   ```

## Open questions for the owner

1. **Where the key lives.** LearnLoop reads `~/.config/learnloop/settings.env`, not the repository-root `settings.env`. Paste the key in the new Settings field, or move it, before relying on hosted GLM-OCR.
2. **The `glm-ocr` extra holds only pypdfium2,** not `glmocr[selfhosted]` as requested. Putting the SDK in LearnLoop's environment conflicts with the `pdf` extra and would move every environment to Pillow 12 (and pulls PyMuPDF, AGPL-3.0). Keep it separate, or declare the conflict and accept the Pillow move?
3. **The token estimate (6,000 per page)** is a guess until a live run reports usage; adjust it after the first keyed import.
4. **Every import using hosted GLM-OCR asks for the whole-file OK,** not only Adds, because GLM-OCR is now the default reader. The OK is once per library.
5. **Desktop reference validators.** `desktop_validate.py` (an unclassified `copy/denyList.ts` from UX Phase 1) and `module_validate.py` (662 missing module notes) already fail at the base commit. Neither is part of this gate and neither was touched.
6. **The hand-written template note** (`Reference/Configuration/learnloop.toml.md`) predates several template changes (it still shows `algorithm_version = "mvp-0.9"` and an older layout). Only its `[ingest.pdf]` lines were updated here; regenerating it from `DEFAULT_CONFIG_TEXT` is a separate chore.

## Second review (2026-10-14)

An independent review of `e5f880778..c13ebeca9` (the whole diff, checked against the glmocr 0.1.5 SDK source in `fixtures-local/glmocr-src.mvnJ`) reported nine findings and five claims in this record and the spec that did not hold. Each finding was first reproduced by a fake-only test that failed on `c13ebeca9` for the reported reason, then fixed. The tests are the `test_r2_*` section of `tests/test_glm_ocr.py` (14 tests, no network: `_open` and the local probe are faked). Two were written after their main fix. The F2 card-path test failed until the card showed a re-read's OK request. The F9 kept-local image test was confirmed to fail with its fix taken out.

| # | Finding | Reproduced (before the fix) | Resolution |
|---|---|---|---|
| F1 (High) | **A kept-local book went to a "local" server on another computer** under an explicit `glm_ocr` engine. `pdf_extractor_for` retried `selected_backend` without `keep_local`, and the guard covered only `backend == "api"`. | With `backend = "local"`, `local_url = http://gpu-box.invalid:5002/...` and a kept-local book, `default_extraction_identity` and `default_extract` did not raise (the extract would have posted the pages there). | `GlmOcrDocumentExtractor.leaves_this_computer()` (z.ai, or a non-loopback `local_url`). `jobs._document_extractor` refuses a kept-local book with `kept_local` (flow `glm_ocr_server`: "reading it here would send it to the text recognition server on another computer"); the same check runs again before every request (F4). A loopback server still reads kept-local books; a book not kept here may use the owner's server without the OK. |
| F2 (Medium) | **With a key, `learnloop import` and Ingest-screen imports failed on the OK** and had no way to give it. | A plain `JobSpec("import", {"source": pdf})` under `auto` failed with `needs_upload_ok`, nothing read. | Under `auto`, an import that cannot show an OK card (no `require_upload_ok`: the CLI, the Ingest screen, a repair) and lacks the z.ai OK reads locally (local Marker, else pypdf; never hosted Marker), flagged `glm_ocr_needs_upload_ok`, as the legacy path does. The card says "This is a plainer reading — text recognition can read it better" with "Read it with text recognition", which re-reads through the Add path and asks the OK on the card. The end-to-end test found a second gap: a book that already had a reading never showed its re-read's OK request (the card looked only at the completed reading), so "Read it with text recognition" was a dead end. The card now shows the latest import's `needs_upload_ok`. An explicit `glm_ocr` engine still refuses rather than switch, now saying "Add it from the Library to say OK, or choose another PDF engine". The Ingest screen's preview matches: a PDF under `auto` without the OK previews as the local reader with no upload. **Rejected part:** an OK action on the Ingest screen and the CLI, and finding import jobs through `result`/`_revision_id`. Once `auto` reads locally neither is needed, and both widen the change. |
| F3 (Medium) | **Any earlier whole-file OK silently covered z.ai.** | A library with `ai.consent.whole_files` (an OK to transcribe a recording, or to send a PDF to "your AI") uploaded to z.ai on Add with no prompt. | z.ai has its own record, `ai.consent.whole_files_zai` (`GLM_OCR_UPLOAD_CONSENT`). `file_upload_allowed(config, flow)` checks the record for the flow, and the guard, the legacy path and the preview use it. The card's OK records the OK that its line named (`pending_upload_flow` reads the waiting import's flow). Neither OK covers the other. |
| F4 (Medium) | **Cancelling, or "Keep this book on this computer", did not stop the remaining windows.** | With a 65-page book (three windows), a batch cancelled after the first window, or the book kept local after it, still sent all three. | `ExtractionContext.interrupt` (with `checkpoints`, a runtime hook that is never hashed) is called before every request, retries included. The import's hook raises `SpendCancelled` on cancellation (never a fallback; the runner records the job as cancelled), and `kept_local` when `repo.source_kept_local` now says so (`handle_import` keeps `_source_id` for it). A request already under way is not recalled, as `keep_on_this_computer` says. |
| F5 (Low) | **A failure part-way threw away the paid windows**, timeouts were never retried, and the 180 s default was under the SDK's 300 s. | Window 3 of 3 failing, then "Try again", sent all three windows again (6 requests). A first timeout failed at once. | Hosted windows are checkpointed in `model_work_checkpoints` (purpose `glm_ocr_window`). The key is the file's SHA-256, the pages, the backend and its models; endpoint, timeout, price and mapping are left out. A retry or a re-read sends only the windows not yet answered (4 requests), and a stored answer that no longer reads is asked again. Each window's answer is checked before the next window is sent, so a malformed answer stops at window 1 instead of after the book. A timeout is retried once. `request_timeout_seconds` defaults to 300, the SDK's `MaaSConfig.request_timeout` (`config.py`, `config.yaml`). All fourteen defaults snapshots were recomputed. |
| F6 (Low) | **`http.client.HTTPException` (IncompleteRead, BadStatusLine, LineTooLong) and pdfium errors escaped the fallback.** | An `IncompleteRead` from `response.read()` raised raw; `_render_pages` on a broken PDF raised `PdfiumError`. | Both become `GlmOcrExtractionError` ("GLM-OCR's answer was cut off" / "Could not render the PDF's pages…"), so under `auto` they fall back. |
| F7 (Low) | **A stand-in run was stored with GLM-OCR's model versions.** | A GLM failure read by pypdf stored `extractor=pypdf` with `{"backend": "api", "recognition": …, "layout": …}`. | `jobs._actual_model_versions`: when the IR carries `<chosen>_failed_<actual>_fallback`, the run (and its actual request hash) records the stand-in's versions plus `fallback_from` (`extractors.fallback_model_versions`). `fallback_from` also keeps a stand-in run separate from the same extractor chosen directly. This also applies to the older Marker→pypdf fallback: such a run now hashes differently, so re-importing that book reads it once more with pypdf (local, free) instead of reusing the old run. |
| F8 (Low) | **Region `width`/`height` were preferred over `data_info.pages`.** | A region whose own size was 980×159 on a 1224×1584 page was clamped to `[76.19, 787.02, 612.0, 792.0]`. | `data_info.pages` first (the only size the SDK's `_maas_response_to_pipeline_result` scales by); a region's size only when that is missing. |
| F9 (Low) | **A kept-local scan said "isn't set up… paste a z.ai API key"** even with a key saved. | The failure line and the health line offered "Set it up" with the key how-to for a kept-local book. | Kept-local books get "This book is never sent to an AI, so only text recognition running on this computer could read the words of a scan", with no action. Like every kept-local line it says "never sent to an AI", not "kept on this computer" (`test_ux_phase1_finish::test_6`; the first full-suite run caught the first wording). A kept-local image that no local reader can read now refuses as `kept_local` ("Never sent to an AI — this image can't be read here") instead of "Text recognition isn't set up". |

**Claims corrected** (the spec's GLM-OCR section is rewritten to match; the lines above in this record stand as written then):

1. **Kept-local books and local servers.** The guard now covers both backends (F1). A local server counts for a kept-local book only on a loopback address, and an explicit `glm_ocr` refuses either backend with `kept_local`.
2. **"Every import using hosted GLM-OCR asks for the OK, worded with z.ai."** Now true, through its own record (F3). Imports that cannot ask read locally under `auto` until it is given (F2).
3. **"The shared envelopes and an automatic build's metered request gate still apply."** This was vacuous: GLM-OCR runs only in import jobs, which install neither. The code comment and the spec now say that a gate in force would apply and that none is installed today. Cancellation is now observed (F4).
4. **"The legacy path's reason is recorded."** It is not. `PdfExtraction.selection_reason` is set, but the legacy ingest (`source_ingestion._pdf_markdown`) keeps only the Markdown and has no health record. The claim is withdrawn and the code is left as it is; adding a health record to the legacy path is outside this change.
5. **"The SDK documents hosted sizes in the region's width/height and in data_info.pages."** It reads only `data_info.pages` (F8). The module docstring is corrected.

**Changed beyond the findings, because a fix needed it:** the book card shows a re-read's `needs_upload_ok` (F2), and the acquisition preview follows the F2 selection.

### Tests

- `tests/test_glm_ocr.py`: 56 tests (42 before). The new `test_r2_*` tests cover:
  - F1: a kept-local book with an explicit engine and a server elsewhere; the same server used by a book that is not kept local; loopback still allowed.
  - F2: a plain import reading locally with its flag and card action; the explicit engine's words; the card's re-read → OK → GLM-OCR path, end to end through the sidecar.
  - F3: an earlier `whole_files` OK never covering z.ai; the card's OK recording `whole_files_zai`; neither OK covering the other.
  - F4: cancellation and keep-local mid-book, through `default_extract`.
  - F5: a timeout retried once; a malformed window stopping the run; checkpointed windows on "Try again" through the durable Add.
  - F6: `IncompleteRead` and an unrenderable page.
  - F7: the stored run's model versions.
  - F8: `data_info.pages` before a region's size.
  - F9: the kept-local failure and health lines, and a kept-local image.
- Updated:
  - the default timeout (300) in the first hosted-request test;
  - four tests now grant `whole_files_zai`, the OK they rely on;
  - the preview test (a PDF without the OK previews locally; an image still names the upload).

### Gate (second review)

The suites ran with `TMPDIR=fixtures-local/tmp` under `flock /tmp/learnloop-fullsuite.lock`, on a machine shared with other worktrees' suites.

- `uv run lint-imports --no-cache`: 17 kept, 0 broken.
- Full suite, first run (`pytest -n auto`): 10663 passed, **1 failed**. `test_ux_phase1_finish::test_6_a_book_never_sent_to_an_ai_says_so_plainly` failed because the two new kept-local sentences said "kept on this computer" or "never sent off this computer". Every kept-local line must say "never sent to an AI" instead (finishing-pass item 6). The sentences and the F9 scan details were reworded.
- Full suite, rerun on the final code: **10664 passed**.
- Durability lane (`pytest -m durability`): **99 passed** (10565 deselected).
- Defaults snapshots: all fourteen recomputed for the 300 s timeout (`test_mvp021_upgrade` passes).
- References:
  - `db_generate_reference.py`, then `db_validate_reference.py`: no errors (the config reference now shows `request_timeout_seconds` = 300; no new configuration leaves).
  - `validate_vault.py`: passed (1102 notes).
- Unchanged, so not rerun:
  - the CLI help snapshot (no CLI change);
  - the frontend and `cargo` (nothing under `apps/` changed).
- No network was used: every GLM-OCR request in the tests goes to a fake `_open`, and the local probe is faked. No key was read or printed.

### Open questions for the owner (second review)

1. **An OK button for explicit-engine imports.** On the Ingest screen or through `learnloop import`, an explicit `glm_ocr` engine without the z.ai OK refuses and points to the Library, because neither surface can give the OK. `auto` no longer needs one. Should the Ingest screen get an OK of its own?
2. **OKs given on this branch before the fix** were stored as `whole_files` and no longer cover z.ai, so each such library asks once more. Only scratch libraries made on this branch are affected.
3. **Window checkpoints are kept indefinitely.** `model_work_checkpoints` has no pruning. A 600-page book keeps 20 window answers, which hold its recognised text (also stored in its extraction). Should old ones be pruned, for example when the book is removed?
4. **Older Marker→pypdf fallback runs re-read once.** Because of F7, a book whose Marker run fell back to pypdf is read once more by pypdf on its next re-import. This happens locally, costs nothing and is reused from then on.

## Third review (2026-10-14)

A verification pass over the second-review fixes (`c13ebeca9..267e80156`) confirmed F1, F3, F4 (stopping uploads), F5, F6, F8 and F9. It found F2 and F7 only partly fixed and reported five new findings (F10–F14), plus five claims in this record and the spec that did not hold. Each finding was first reproduced by a fake-only test that failed on `267e80156` for the reported reason, then fixed. After the owner's pause (2026-10-14, 02:20 to 09:00) this was checked again: the nine original `test_r3_*` tests were run against an export of `267e80156` (`git archive`, nothing in the worktree touched), and all nine failed for the reported reasons. The verifier's own six reproductions were also rerun on the fixed tree. The three that assert the bug (F10, F11, F7) now fail on those lines. The other three assert only that nothing was sent, which still holds, and their printed outcomes show the fixes. Finishing F10 found one more gap (an image, below), reproduced and fixed the same way. No network was used.

| # | Finding | Reproduced (before the fix) | Resolution |
|---|---|---|---|
| F10 (High) | **A "local" extraction repair sent a book's pages to z.ai**, a kept-local book's too. `handle_extraction_repair` never set `_keep_local` or `_source_id`, and nothing read the repair's consent (`provider: "local"`, `external: false`). | With a z.ai key and the z.ai OK, a local repair of a kept-local link book (and of a book not kept local) was read by `glm_ocr`. Under `engine = "glm_ocr"` the same happened. | The repair now sets `_keep_local` (the book's stored choice), `_source_id` (read again before each request) and `_local_repair` (`jobs._repair_is_local`: `external` false or provider `local`; a record without `external` counts as local). `jobs._local_only` (kept local, or a local repair) drives selection: `auto` passes over z.ai and non-loopback servers, native becomes `auto` and hosted Marker becomes pypdf, as for a kept-local book. Under an explicit `glm_ocr` engine, a local repair is read by `local_pdf_extractor` (local Marker, else pypdf). An external repair of a kept-local book still never uploads: `auto` passes over z.ai and an explicit engine refuses with `kept_local`. **Found while finishing it:** a local repair of an *image* under an explicit `glm_ocr` engine still went to z.ai. Only GLM-OCR reads an image, so the local branch skipped it, and the upload guard passed once the z.ai OK existed. With the Add's stored window answer cleared (a repair of other pages has none), the reproduction sent one request carrying the PNG. Under `auto` nothing was sent, but the learner was told "Text recognition needs a z.ai API key…" with a key set. Now both refuse with `local_repair`: "Only text recognition can read an image, and none runs on this computer, where this repair was asked to stay. Turn on "external VLM" to repair it…". A kept-local image is still refused as `kept_local`, and a server on this computer still reads it. |
| F2 (Medium, residual) | **A scan or an image imported from the Ingest screen or `learnloop import` with a key but no OK dead-ended.** The card was silent because the failed import named no book, and a scan was told to install marker-pdf. | A plain import of a blank-page PDF failed with `PyPdfExtractionError` ("…install marker-pdf…"). A PNG failed with `needs_upload_ok` ("…or choose another PDF engine"). In both cases the library card had no line and the pending list was empty. | (1) `handle_import` names its book on the job (`_record_import_source`: payload `source_id`, written once after `_apply_requested_keep_local`), so `ingest_jobs_for_source` finds an import that failed after registering its book. (2) Under `auto`, when a PDF was read locally only because the z.ai OK was missing (`glm_ocr_needs_upload_ok`) and that reading finds no text, the import fails with `needs_upload_ok` (flow `glm_ocr_upload`). Its message says the PDF looks scanned and asks for the OK on its card in the Library. A repair keeps the local reading's error, because no card asks for a repair's OK. (3) An image's message no longer mentions another PDF engine. The card then shows "Reading this document sends the whole file to z.ai (GLM-OCR)" with OK, and the OK resumes the import, which reads it with GLM-OCR (end to end through the sidecar, for both a scan and an image). |
| F11 (Medium) | **"Never send this book to an AI" during a hosted read left a readable book unreadable**, with a false "can't be read here" line and no action. | A 65-page book, kept local after window 1, failed with `kept_local`. Its card said "Never sent to an AI — this PDF can't be read here"; resuming read it locally. | Under `auto`, for a PDF, the interrupt raises `GlmOcrKeptLocal` (a `GlmOcrExtractionError`), so `extract_with_fallback` reads the rest on this computer. The flag is `glm_ocr_kept_local_<engine>_fallback`, not `_failed_`, so the card never says text recognition failed. The stored run records the stand-in's versions with `fallback_from`. An explicit engine, or an image (only GLM-OCR reads one), still refuses with `kept_local`. Cancellation and spend refusals still never fall back. `test_r2_f4` now uses an explicit engine for its keep-local half. |
| F7 (Low, residual) | **A double fallback stored GLM-OCR's model versions on a pypdf run.** | GLM-OCR offline and Marker failing gave the flags `glm_ocr_failed_marker_fallback` and `marker_failed_pypdf_fallback`, and a pypdf run with `{"backend": "api", …}`. | `_actual_model_versions` matches any `<chosen>_failed_…_fallback` or `<chosen>_kept_local_…_fallback` flag, not only the one naming the final extractor. The run stores `{"fallback_from": "glm_ocr"}` (pypdf has no model versions). |
| F12 (Low) | **A pending z.ai OK stuck to a book after it was kept on this computer.** Tapping it would record the library-wide z.ai OK. | A book with a local reading: "Read it with text recognition", then "Never send this PDF to an AI". The card still offered the OK. | The card never offers an upload OK for a kept-local book. `keep_on_this_computer` stops a re-read that waits for an OK (cancels its batch). For a book never read, it resumes the waiting Add under the new choice, so it is read here or refused as never sent to an AI (the test's never-read PDF is read locally at once). The card's waiting-OK line skips a cancelled batch, so letting AI write questions later does not bring the old request back. A kept-local book whose import still waits (only books kept before this fix) says "Never sent to an AI — this PDF hasn't been read yet" with "Try again", which reads it under that choice. **Rejected part:** a "Not now" action that dismisses a waiting re-read. A card's status line carries at most one action (`docs/specs/ux_learnloop_v1.md` §7.2, `BookCard.tsx`), and here that action is the OK. A failed batch has no cancel anywhere in the app today (the Ingest screen cancels only active batches), so a "Not now" would need a new action kind in the sidecar, the DTO and BookCard's details. That widens this change; it is an open question below. |
| F13 (Low) | **A stored window answer that stopped validating was paid for again on every run**, because write-once checkpoints kept the stale answer. | A saved window that today's mapping cannot read made each of two runs send a request. | `_ModelCheckpoints.discard` (`discard_model_checkpoint`, as the inventory and legacy windows do). The extractor discards a stored answer that no longer validates before asking again, and the new answer is saved: two runs, one request. |
| F14 (Low) | **The card's details showed raw flags** (`glm_ocr_needs_upload_ok`, `glm_ocr_failed_*`). | `_health_line` returned the flag as `details`. | Plain details: "It was read on this computer. Reading it with text recognition sends the whole file to z.ai, which asks your OK first." and "Text recognition (GLM-OCR) couldn't be reached or couldn't read it, so it was read on this computer instead." The older `marker_failed_pypdf_fallback` details were not named and are unchanged. |

**Claims corrected** (the spec's GLM-OCR section is updated; the earlier lines of this record stand as written then):

1. **"A book kept on this computer never leaves it for text recognition."** Now true for repairs too (F10), and a repair whose consent is local never leaves this computer, whatever the engine.
2. **"An import with no card to ask on reads a PDF locally … and the book card then offers 'Read it with text recognition'."** That held only for PDFs with a text layer. Scans, images and explicit-engine imports now fail with `needs_upload_ok`, and the book's card asks for the OK, because the import names its book (F2). "A repair" is no longer listed among these imports: a local repair never uploads (F10). An external repair without the OK reads locally, and a scan keeps the local error.
3. **"The stored run records the stand-in's model versions with `fallback_from`."** Now true through a second fallback (F7).
4. **"Refusals (kept on this computer) never fall back."** Under `auto`, a book kept here part-way through is now read here (F11). The other refusals (no OK, spend, cancellation) still never fall back, and an explicit engine still refuses.
5. **"A stored answer that no longer reads is asked again."** It is, once: the stale answer is discarded and replaced (F13).

**Changed beyond the findings, because a fix needed it:** an import now names its book in its payload as soon as the book is registered (F2). As a result, a link Add whose import fails after registering its book shows that failure on the book's card. Before, the book's card had no line and a separate pending card showed the failure. The pending list skips an import that names its book (`pending_adds`), so the failure shows once. F12's fix is not limited to GLM-OCR: a recording whose Add waits for its transcription OK, kept on this computer, has its Add resumed and refused as never sent to an AI, as a recording kept local at Add already was (re-review F13). Its card no longer offers the OK.

### Tests (third review)

- `tests/test_glm_ocr.py`: 67 tests (56 before). The new `test_r3_*` tests cover:
  - F10: local repairs of a kept-local and a shared book, under `auto` and an explicit `glm_ocr` engine; an external repair of a kept-local book; a local repair of an image under either engine (nothing sent, plain refusal).
  - F2: a scan and an image through the Ingest screen's import, then the card's OK, end to end through the sidecar.
  - F11: keep-local after window 1 of a durable Add.
  - F7: GLM-OCR → Marker → pypdf.
  - F12: a waiting re-read and a waiting first Add, each kept local through the card.
  - F13: a stale checkpoint replaced.
  - F14: the details' words.
- Updated: `test_r2_f2` (plain details) and `test_r2_f4` (keep-local mid-read under an explicit engine).
- Checked once, not kept as a test: the recording case in "Changed beyond the findings" (an audio Add waiting for its OK, then kept here through the card). Nothing was sent, the import was refused as `kept_local`, and the card said "Never sent to an AI — this recording can't be read here" with no action.

### Gate (third review)

The suites ran with `TMPDIR=fixtures-local/tmp` under `flock /tmp/learnloop-fullsuite.lock`, on a machine shared with other worktrees' suites.

- `uv run lint-imports --no-cache`: 17 kept, 0 broken.
- Full suite (`pytest -n auto`): **10675 passed** (10664 at the second review, plus the 11 new tests).
  - A first attempt was stopped part-way, unfinished: its log path was shared with another worktree's agent, so its output could not be told apart. It was rerun with a log inside this worktree.
- Durability lane (`pytest -m durability`): **99 passed** (10576 deselected).
- Unchanged, so not rerun:
  - the defaults snapshots and the DB/config references (no migration and no configuration change);
  - the CLI help snapshot (no CLI change);
  - the frontend and `cargo` (nothing under `apps/` changed).
- No network was used: every GLM-OCR request in the tests goes to a fake `_open`. No key was read or printed.

### Open questions for the owner (third review)

1. **"Not now" for a waiting re-read (F12's rejected part).** A book whose "Read it with text recognition" waits for the z.ai OK keeps that line until the OK is given or the book is kept on this computer. Should the card get a way to drop the request? It needs a new action kind and a cancel for a failed batch, which the app does not have today.
2. **Repairs of file-added books fail before they start.** Their `original_uri` is `file://…`, which `resolve_source` refuses. The verifier noted this and it predates this branch; the F10 tests point the revision at a plain path, as a link's URL would be. Fix it separately?
3. **The repair dialog offers a local repair for an image.** That repair is now refused, saying to turn on "external VLM". Should the dialog say so before the learner starts?
4. **Scan detection reads the local reader's error text.** A plain import is told to give the z.ai OK when pypdf's error says "no extractable text" or "likely scanned" (`jobs._found_no_text`). `test_r3_f2…[scan]` fails if that wording changes, but a typed "no text layer" error from the extractors would be sturdier. Worth it?

## Landing onto main

**Branch:** `merge/glmocr-onto-main` (worktree `learnanything-merge2`), from main `6dabbc33c` (`mvp-0.23`, LATEST; reading hardening, RW3a, router R2a and the tutor delivery fixes landed). Not pushed. Owner-directed, 2026-10-14, single phase: merge `fcf7dc95d`, references `55709da33`, a prose fix `49de4a79b` (below), this record. `ingest/glm-ocr` (`3556a4977`) and its worktree `learnanything-glmocr` were not modified.

**Main since this branch's base `e5f880778`** (exam protection, one predicate in `content/sources/exam_material.py`, was already in the base):
- reading hardening (`db30696ba`..`4cf54a295`): the level-triggered reading sweep (30 s), one check-offer rule in `checkOffer.ts`, the scanned-PDF lines without their kept-local variants, and **the retired per-book keep-local**;
- the contextual-embeddings experiment spec (docs only);
- RW3a (Reader hooks, margin cues, `[cues]`) and router R2a (`mvp-0.23`, migration 202, fifteen defaults snapshots), landed together;
- the tutor delivery fixes (`275fd5f7e`..`6dabbc33c`): complete source blocks for the tutor, and `queue_source_vectors(ctx, extraction_id)` after every completed extraction in `handle_import` and `handle_extraction_repair`.

**Paid calls:** none ($0.00); no network, no key read. **Migration:** none (head 202 is main's). **Algorithm version:** unchanged, no successor (document extraction only; replay reads none of it). **Config:** `[ingest.pdf.glm_ocr]` (8 leaves) beside main's keys: 837 effective leaves in 50 sections. **RPC:** `set_text_recognition_api_key`, desktop only. **Frontend / `src-tauri`:** changed (the Settings key field and its Tauri passthrough), so both gates ran.

### Conflicts

| File | Resolution |
|---|---|
| `src/learnloop/config/template.py` (14 hunks) | Main's R2a, RW3a and tutor-delivery notes kept, and the branch's added: its full note after the tutor-delivery note in `mvp-0.9` (now "all fourteen ... on its branch ..., and all fifteen again from the composed defaults when it landed after router R2a, RW3a and the tutor delivery fixes"), its "moves it too" line in `mvp-0.10`..`mvp-0.22`, and the same line added to `mvp-0.23`, which the branch never saw. All fifteen hashes recomputed (template `.pyc` deleted, `config/template.py` touched; `test_config_refactor.py` then passes in a fresh process). |
| `src/learnloop/content/pipeline/jobs.py` (5 hunks) | The keep-local composition (next section); `_actual_model_versions` placed beside main's `queue_source_vectors`, `handle_source_embedding_backfill` and `_source_vectors_failure`, all kept. |
| `src/learnloop/content/pipeline/add_source.py` (8 hunks) | The keep-local composition: `keep_on_this_computer` and `share_with_ai` stay deleted (main); the branch's `_import_waiting_for_upload_ok`, `GLM_OCR_UPLOAD_CONSENT`, `pending_upload_flow`, the GLM card lines and `text_recognition_available(config=)` kept without their `keep_local` parameters. |
| `src/learnloop_sidecar/handlers/first_run.py`, `handlers/ingest.py` | `text_recognition_available(config=vault.config)`, one value per library (no per-book variant). |
| `tests/test_mobile_allowlist.py` | `ROUTER_R2A_RPCS + GLM_OCR_RPCS + GLM_OCR_EXTENDED_RPCS`: `set_text_recognition_api_key` pinned desktop only, and `update_ingest_settings`, `start_ingest`, `start_import_batch` (the `glm_ocr` engine) too. |
| 372 notes under `Reference/` | Taken from main, then regenerated (below). |

### The keep-local composition

**Main's rule (owner, 2026-10-13; reading hardening part 3):** it is fine to send books to an AI, and there is no per-book opt-out. `add_source.keepLocal`, the `keep_local` / `share_with_ai` actions and `AddSourceOptions.keep_local` / `keep_on_this_computer` / `share_with_ai` are gone; `source_artifacts.keep_local` stays as a column that nothing consults, and doctor warns `source:retired_keep_local`. This branch was cut before that and built several fixes on keep-local. Each was composed to main's model:

| Branch piece | What it did on the branch | After the landing |
|---|---|---|
| `jobs._kept_local`, `ctx.job["_keep_local"]` (set by `handle_import` from `repo.source_kept_local` and by the repair), `_apply_requested_keep_local` | the book's stored choice (or the Add's request) | **Removed.** `handle_import` sets neither `_keep_local` nor `_source_id`; nothing reads `source_artifacts.keep_local` (main's `test_nothing_in_src_consults_the_retired_keep_local` and `test_keep_local_retired.py` pass unchanged). |
| `_local_only(ctx)` = kept local **or** a local repair | narrowed `_pdf_payload_config` (native → auto, hosted Marker → pypdf) and selection | **`_local_repair(ctx)`**: a local repair only. |
| `selected_backend(..., keep_local=)`, `pdf_extractor_for(..., keep_local=)` | `auto` passed over z.ai and a non-loopback server | Renamed **`local_only=`**, passed only for a local repair. |
| `_guard_file_upload`'s kept-local refusal and `_KEPT_LOCAL_FLOW_MESSAGES` (`glm_ocr_upload`, `glm_ocr_server`, `glm_ocr_image`) | refused with `kept_local` | **Removed** (main had already removed the guard's refusal and its messages). The z.ai OK logic is kept: z.ai's upload always asks for its own OK (`whole_files_zai`), and a plain import's words say where it is given. |
| `_document_extractor`: the kept-local image refusal (second review F9) and the explicit-engine refusal of a server elsewhere (F1) | refused with `kept_local` | **Removed.** F1's guard now serves a local repair: an explicit `glm_ocr` with a server on another computer is read by local Marker, else pypdf. |
| `_extraction_interrupt`'s keep-local half, `_kept_local_now`, `GlmOcrKeptLocal` and the `glm_ocr_kept_local_<engine>_fallback` flag (F4's second half, third review F11) | stopped the windows not yet sent when a book was kept here part-way | **Removed.** The interrupt checks cancellation only (F4 kept). `extract_with_fallback` flags only `<chosen>_failed_<engine>_fallback`, and `_actual_model_versions` matches only that. |
| Third review F12: `keep_on_this_computer` resuming or cancelling an import waiting for the OK; the kept-local "hasn't been read yet" line; the waiting-OK line skipped for kept-local books | | **Removed** with `keep_on_this_computer` (main). `_import_waiting_for_upload_ok` stays: every book's card shows a re-read waiting for its OK (second review F2). |
| F9's kept-local scan lines (`_SCAN_DETAILS_KEPT_LOCAL`, `_scan_unreadable(keep_local)`), `_import_failure_line(keep_local=)`, `_health_line` reading `source_kept_local`, `text_recognition_available(keep_local=)` | "never sent to an AI" variants with no action | **Removed.** A scan's line offers "Read it with text recognition" when GLM-OCR or Marker can run, else "Set it up" with the key how-to. |
| The text-recognition re-read (`enqueue_add_source`): `selected_backend(keep_local=chosen.keep_local)`; the shelf's per-keep-local availability; `source_action`'s read of `artifact["keep_local"]` | | `selected_backend(glm_settings)`; one availability per library. |

**Kept:** the one-time whole-file OK naming z.ai (`ai.consent.whole_files_zai`, its own record, F3), the card's OK recording the flow its line named (`pending_upload_flow`), and the consent at AI connection.

**Repair consent.** Main still offers an explicit local repair: OutlineAndPlan's repair dialog without "external VLM" sends `provider: "local", external: false` ("I consent to re-running local extraction for repair"), and `learnloop repair-extraction` without `--use-llm` does the same. So the third review's F10 stays for that choice: `_repair_is_local(consent)` sets `ctx.job["_local_repair"]`, and such a repair never uploads whatever the engine (native → auto, hosted Marker → pypdf, `auto` passes over z.ai and a non-loopback server, an explicit `glm_ocr` is read by local Marker, else pypdf, and an image is refused with `local_repair`, pointing to "external VLM"). An external repair is treated like any other reading: under `auto` with the z.ai OK it goes to z.ai (now tested; on the branch the kept-local book had masked that case), and without the OK it reads locally.

**Kept unchanged (they never depended on keep-local):** model versions after a double fallback (F7), the scan → `needs_upload_ok` card flow and an import naming its book (F2), cancellation (F4), window checkpoints and their replacement (F5, F13), cut-off answers and unrenderable pages (F6), `data_info.pages` first (F8), plain card details (F14), hash-stable request config, pixel boxes and the self-hosted multi-image response.

**Docs composed too:** the ingestion spec's privacy paragraph (no per-book opt-out; a local repair is the one local-only reading); the reference generator's `backend` and `local_url` notes ("a repair OK'd as local" instead of the kept-local book); comments in `glm_ocr.py`, `extractors/base.py` and `extractors/__init__.py`.

**Tests (`tests/test_glm_ocr.py`, 67 collected before and after):**

| Test | Change | Why |
|---|---|---|
| `test_r2_f9_a_kept_local_image_is_refused_as_kept_here_not_as_unset` | removed | The `kept_local` refusal is retired. An image without GLM-OCR is covered by `test_an_image_import_needs_glm_and_reads_with_it`, a local repair of an image by `test_r3_f10_..._of_an_image_...`. |
| `test_r3_f11_keeping_a_book_here_mid_read_reads_the_rest_here` | removed | There is no per-book choice to make part-way; `GlmOcrKeptLocal` is gone. |
| `test_r3_f12_a_book_kept_here_never_asks_for_the_z_ai_ok` | removed | `source_action`'s `keep_local` is a validation error on main (`test_keep_local_retired.py`). |
| `test_a_kept_local_book_never_goes_to_z_ai` | replaced by `test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other` | A book whose `source_artifacts.keep_local` is set asks for the z.ai OK on its card like any other and is read by GLM-OCR after it; a stale `keep_local` on the job or payload changes nothing under an explicit engine. |
| `test_local_runs_only_when_chosen_and_answering_and_a_kept_local_book_never_uploads` | adapted → `..._a_local_only_reading_never_uploads` | `local_only=`. |
| `test_read_again_with_text_recognition_uses_glm_when_it_can` | adapted | The kept-local variant dropped; without a key the re-read names Marker. |
| `test_r2_f1_a_kept_local_book_never_goes_to_a_glm_server_on_another_computer` | adapted → `test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer` | The same guard, for a local repair: read by pypdf, nothing sent; any other reading may use the owner's server; a loopback server still serves a local repair. |
| `test_r2_f9_a_kept_local_scan_never_asks_for_a_key_that_cannot_help` | adapted → `test_r2_f9_a_scan_offers_text_recognition_or_where_to_set_it_up` | The kept-local lines are gone; the scan's two lines remain. |
| `test_r2_f4_cancelling_or_keeping_it_here_stops_the_windows_not_yet_sent` | adapted → `test_r2_f4_cancelling_stops_the_windows_not_yet_sent` | The keep-here half is retired. |
| `test_r3_f10_a_local_repair_never_leaves_this_computer` (both engines) | adapted | One book instead of a kept-local and a shared one: a local repair is read by pypdf with nothing sent; an external repair, the OK given, goes to z.ai (one request). |
| `test_r3_f14_the_cards_details_are_plain_words` | adapted | The fake repository no longer needs `source_kept_local`. |
| `test_every_glm_ocr_reading_queues_the_source_block_backfill` (3 cases) | added | The tutor-delivery composition, below. |

`tests/test_keep_local_retired.py` (8) and `tests/test_reading_hardening_landing.py` (4) pass unchanged.

### Other compositions

- **Tutor delivery fixes.** Both branches edited `handle_import` and `handle_extraction_repair`. `queue_source_vectors` stays where main put it, after the extraction completes (fresh or reused) in both. Every GLM-OCR reading of an import ends in `handle_import`'s one persistence block: a hosted read in windows, a stand-in reading after a GLM-OCR failure (Marker, pypdf, or both), and a scan read after its OK (the resumed import). So each queues its source's block-vector backfill when both embedding switches are on. `test_every_glm_ocr_reading_queues_the_source_block_backfill[hosted_windows|fallback|scan_after_the_ok]` checks this with a hashing embedder: one `source_embedding_backfill` job for the import's extraction, completed. The branch's `_actual_model_versions` changes only the stored model versions and request hash, not where the run completes. GLM-OCR's blocks pass `classify_block_role` like the other extractors' blocks, so the delivery's numbered labels and references ("Theorem 3.2", "by 1.32") read them the same way.
- **Reading hardening, besides keep-local.** The 30 s reading sweep acts on reading requests, which need a book with a reading. A re-read waiting for the z.ai OK is queued with `auto_build` off (the book already has a reading), and an Add waiting for the OK leaves its planner blocked, not active, so neither holds a request as "unfinished work". The scanned-PDF lines: since the base, main changed them only to drop the kept-local variants (and `text_recognition_available`'s `keep_local`). The merged lines are the branch's without a kept-local variant: the how-to names the z.ai key, and the card's one action is "Read it with text recognition" where GLM-OCR or Marker can run, else "Set it up". `checkOffer.ts` is untouched.
- **Exam protection** (in the base). GLM-OCR writes ordinary IR (units, blocks, spans), so `exam_material`'s predicate, the corpus exclusions and held-out selection apply to its readings unchanged.
- **R2a, RW3a, the contextual-embeddings spec.** No shared code: GLM-OCR adds no plan, router or Reader-cue path. The fifteen defaults snapshots and the template notes are composed (Conflicts).
- **Optional extras.** The `glm-ocr` extra holds only pypdfium2. `glmocr[selfhosted]` (transformers ≥ 5, Pillow ≥ 12) conflicts with `marker-pdf`, so the SDK stays in its own environment; `uv lock --check --offline` agrees with `pyproject.toml`.
- **Pipeline Map.** The ingest diagram and the extraction line name GLM-OCR as the primary reader (z.ai or a self-hosted glmocr server, after the OK naming z.ai), with local Marker and then pypdf as fallbacks, and link this record.

### References

- `db_generate_reference.py` (`55709da33`): schema head 202, 321 table notes, 837 configuration leaves in 50 sections (829 on main plus `[ingest.pdf.glm_ocr]`'s 8).
- Prose counts: `Configuration.md`'s catalog line and `Database.md`'s validator line, 829 became 837.
- `db_validate_reference.py`: errors `[]`. `validate_vault.py`: passed, 1105 notes.

### Gate

Run in this worktree with `TMPDIR=<worktree>/fixtures-local/tmp`; the suites at `49de4a79b` under `flock /tmp/learnloop-fullsuite.lock`, on a machine shared with other worktrees' suites.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts 5.14.0 back); `uv lock --check --offline` agrees with `pyproject.toml` |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** (the branch's three `ingest -> ai.spend/ai.execution` exemptions beside main's) |
| `uv run pytest -n auto` | **10,965 passed, 0 failed**, 49 warnings (14 min 31 s) |
| `uv run pytest -m durability` | **100 passed**, 10,865 deselected, 1 warning (1 min 51 s) |
| Frontend (`apps/learnloop-tauri`) | `npm install` ok; `npm run typecheck` clean; `npm test` **575 passed** (81 files); `npm run frontend:build` built (the usual chunk-size note) |
| `cargo check` (`src-tauri`) | clean |
| Defaults | all 15 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed (each moved); `test_config_refactor.py` 34 passed in a fresh process |
| CLI help | `python tests/test_cli_help_snapshot.py --write`: `ingest` and `ingest-exam` (the `glm_ocr` engine in `--pdf-engine`) |
| References | above; `git diff --check 6dabbc33c HEAD` clean |

**Targeted runs before the gate** (on the composed tree): `test_glm_ocr.py`, `test_keep_local_retired.py`, `test_pdf_extractor_selection.py`, `test_mobile_allowlist.py`, `test_cli_help_snapshot.py`, `test_config_refactor.py`, `test_desktop_rpc_contract.py` and `test_ingest_runner.py`: 300 passed once the snapshots were recomputed (the first run read a stale template `.pyc`: the recompute rewrites hashes of the same length within the same second, which is why the procedure deletes the `.pyc` and touches the file). Then `test_reading_hardening_landing.py`'s source scan caught the composed `_local_repair` docstring naming `source_artifacts.keep_local` (`jobs.py` is not on its prose allow-list); `49de4a79b` rewords it (same line count, so the references' citations hold), and that file and `test_keep_local_retired.py` pass (12).

**The known flake did not show:** `test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]` passed in the full run.

**One warning is new to the landing runs (48 before, 49 here), and it is main's.** A `PytestUnhandledThreadExceptionWarning`: a `learnloop-reading-sweep` thread ran its pass while `test_success_head.py::test_deterministic_rebuild_and_no_store_or_network` had `sqlite3.connect` patched to fail ("store access"). The thread came from an earlier test on the same xdist worker: `SidecarContext.load` binds the ingest host in the background, which starts the sweep; a test that then rebinds it foreground leaves the thread alive until its host is collected, and its first pass comes one 30 s pace later. That is reading hardening's sweep and two of main's tests, and it depends on timing. GLM-OCR starts no sweep, though its sidecar tests add a few more such loads. It is a warning, not a failure, and is left to reading hardening's owner (question 8 below).

### Parity

**Copies.** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`), in `fixtures-local/glm-parity`.

**Migration, each copy by its own code** (`migration_coordinator.migrate_vault`), 47 migrations each, to head 202:
- main `6dabbc33c`: `src`, `migrations` and `pyproject.toml`, exported with `git archive` and run on `PYTHONPATH` (the run printed the archive's `learnloop/__init__.py`);
- the merge: this worktree's own code (at `55709da33`; `49de4a79b` changes one docstring only).

**Runs.** On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json`, with `LEARNLOOP_CONFIG_DIR` an empty directory (no key found, nothing sent).

**Result: 0 replay differences, and doctor identical.** Once ULIDs, timestamps, ids, hashes and the copy's path are set aside, the shadow rebuilds and the doctor reports match exactly on both fixtures.

| Fixture | Replayed attempts | Facet | Mastery | Schedule | Doctor issues | Errors | `criterion:unknown_dependency` |
|---|---:|---:|---:|---:|---:|---:|---:|
| linear algebra | 70 | 22 | 6 | 47 | 106 | 1 | none |
| probability | 2 | 2 | 1 | 1 | 134 | 49 | 46 |

These are the fixtures' existing drift at `mvp-0.8`, the same figures as the tutor-delivery landing. Neither fixture carries the retired keep-local, so doctor raises no `source:retired_keep_local`. `live_database.unchanged` is true on every run, each copy's `state.sqlite` hash is the same before and after its runs, and doctor exits 1 on both sides, as on main. The tracked fixtures were only copied: `git status fixtures/` is clean.

### Safety

- No paid call, no real provider, no network. No key, credential, `.env` or `settings.env` file was read, nor `~/.config/learnloop/`.
- The main checkout was not touched. The tracked fixtures were opened only by the backup API, to copy them.
- Nothing was pushed, rebased or stashed. `ingest/glm-ocr` and `learnanything-glmocr` were not modified.

### Open questions for the owner (defaults applied)

1. **The z.ai key (needed before any hosted reading).** The app reads keys only from `~/.config/learnloop/settings.env`, the shell environment or the vault's `.env`, never the repository-root `settings.env`. Add `ZAI_API_KEY=…` to `~/.config/learnloop/settings.env`, or paste the key in **Settings → Ingestion → "text recognition key"**. Then the live check above ("Rerun with the key") can run, about **$0.002**; its scratch vault and the two documents are in `learnanything-glmocr/fixtures-local`, and the code it needs is on main now. **Default:** no key, so `auto` reads with local Marker, else pypdf, recording why in health.
2. **The glmocr SDK stays in its own environment.** The `glm-ocr` extra holds only pypdfium2; `glmocr[selfhosted]` would move every environment to Pillow 12 and transformers 5, which `marker-pdf` refuses. **Default:** kept separate (see "Run GLM-OCR locally").
3. **6,000 tokens per page** (`ESTIMATED_TOKENS_PER_PAGE`) stays the preview estimate until a keyed run reports real usage. **Default:** 6,000; adjust after the first keyed import.
4. **Hosted reads ask the one-time OK once.** Every import that would send a file to z.ai waits for the OK naming z.ai, once per library (`whole_files_zai`); an import that cannot show the card reads a PDF locally meanwhile. **Default:** as built.
5. **Bounding-box units are confirmed by the first keyed run.** The hosted `bbox_2d` is read as pixels of z.ai's page render (the SDK's reading), scaled by `data_info.pages`. **Default:** as built; health records the shape seen (`glm_ocr_response_*`), and a differing live shape becomes a fixture in `tests/test_glm_ocr.py`.
6. **A waiting re-read has no "Not now"** (third review, question 1). With keep-local retired, giving the OK is now the only way a book's "Read it with text recognition" request stops asking. **Default:** unchanged; a "Not now" needs a new action kind and a cancel for a failed batch.
7. The second and third reviews' other questions stand as written (OK buttons for explicit-engine imports, checkpoint pruning, repairs of file-added books, the repair dialog for an image, typed scan detection).
8. **The reading sweep's leftover thread (not this branch's).** See Gate: a sweep started by `SidecarContext.load` outlives a test that rebinds its host foreground. **Recommended** for reading hardening's owner: a rebind to the foreground stops the sweep it started, or `test_success_head` patches only its own connections.
