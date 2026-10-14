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
