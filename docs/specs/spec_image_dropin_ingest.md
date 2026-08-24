# Image drop-in ingest (photo → practice item)

Status: proposed.
Scope: a new capture path — drop or paste a phone photo/screenshot of a single
problem (e.g. a technical-interview question) into the ingest screen and turn
it into a reviewed practice item in the active vault, with the photo kept as
provenance. Transcription routes to the existing `codex_low` subscription
profile now; an OpenAI-compatible VLM provider is a config-only addition later,
and that same endpoint doubles as marker-pdf's VLM boost for hard documents.

Out of scope: any mobile app or share-sheet story (phone → desktop transfer is
the user's problem: sync folder, KDE Connect, note-to-self), multi-problem
segmentation of one photo, and treating the image itself as the canonical item
stimulus (see §6 for the diagram escape hatch).

## 1. Journey

1. **Drop / paste.** The learner drags a `.png/.jpg/...` onto the Ingest
   screen (or pastes a clipboard image, slice 2). It stages like any other
   source, with a thumbnail.
2. **Crop (slice 2).** Optional in-app crop before anything is stored. Slice 1
   assumes the phone did the cropping.
3. **Transcribe.** A durable job sends the image + a transcription prompt to
   the provider routed for the new `image_transcription` task — `codex_low`
   (gpt-5.6-sol, low effort, ChatGPT subscription auth) by default. Output is
   structured: markdown transcript (LaTeX math, fenced code) + a
   `diagram_present` flag.
4. **Review (mandatory).** Side-by-side photo and editable transcript. Vision
   transcription of code/math from phone photos will have errors; a subtly
   wrong problem statement poisons the item forever, so there is no
   auto-accept path.
5. **Item.** The confirmed transcript becomes the source revision text and
   rides the existing quick-add flow (`plan_quick_add` → `confirm_quick_add`)
   into one proposed practice item, scoped to the chosen subject. The photo
   remains viewable from the item via provenance.

## 2. Source type: `image`

- `src/learnloop/ingest/resolution.py`: add `image` to `SourceCategory`;
  `resolve_source` accepts suffixes `.png .jpg .jpeg .webp .heic`.
  `detect.py` follows for free.
- `src/learnloop/ingest/fetchers.py`: new `fetch_image` — reads bytes,
  sniffs/validates the media type, rejects images over a sanity cap
  (~20 MB), returns them for registration. No text extraction happens here.
- **Originals store.** Bytes go through the existing content-addressed
  `store_original_bytes` (`ingest/originals.py`) exactly like PDFs.
  Constraint: `canonical-sources/raw/sha256-<hex>` names are extensionless,
  and both the Codex `localImage` input and OS-level viewers want a real
  image path. Registration therefore also records the media type on the
  source revision, and callers that need a typed path materialise a
  `sha256-<hex>.<ext>` copy under `.learnloop/source-cache/images/` (cheap,
  content-addressed, safe to regenerate).
- **Serving to the UI.** Generalise the `llpdf://` handler in
  `apps/learnloop-tauri/src-tauri/src/main.rs` into asset serving that also
  returns image media types (same content-hash-only path rule). Either keep
  the scheme name or add a sibling `llimg://`; reuse the existing CSP
  allowance pattern from `tauri.conf.json`.
- **No schema migration expected.** `source_artifacts` / `source_revisions`
  already carry `asset_hash` + `original_uri`, and the transcript is stored
  as a normal extraction run (§4). If a flag does become necessary, the next
  free migration number is 110 (verify with `ls migrations/` first).

## 3. Transcription task and provider routing

- **New task.** Add `"image_transcription"` to `AITask`
  (`src/learnloop/ai/routing.py`) and to `DEFAULT_CODEX_TASK_ROUTES` /
  `[ai.routing]` defaults (`config.py`) routed to `codex_low`. The existing
  `provider_for_task` / `LEARNLOOP_AI_PROVIDER` / explicit-provider machinery
  applies unchanged, so pointing the task at a future VLM profile is a
  one-line config edit.
- **Multimodal transport (the only real infra change).**
  `SdkCodexClient._run_structured` (`src/learnloop/codex/client.py:942`)
  currently passes a bare prompt string. The SDK's `Thread.run` accepts
  `RunInput = str | list[InputItem]` where `InputItem` includes
  `LocalImageInput` (verified in the checkout at
  `sdk/python/src/openai_codex/_inputs.py`, wired to `{"type": "localImage",
  "path": ...}`). Extend `_run_structured` with an optional
  `image_paths: list[str]` kwarg; when present, send
  `[TextInput(prompt), LocalImageInput(path=...), ...]`. Pass the typed
  cache path from §2, never the extensionless raw path.
- **Client method.** `run_image_transcription(context) ->
  ImageTranscription` on `SdkCodexClient`, discovered via
  `getattr(client, "run_image_transcription", None)` — the same
  degradation contract as `run_diagnostic_trials`. Unlike those tasks there
  is no deterministic fallback: a provider without the method fails the job
  with a clear `provider_lacks_vision` error naming the routed provider.
- **Output schema** (`codex/schemas.py`), enforced via the existing
  `output_schema` path — keep it small; low-effort models follow small
  schemas best:

  ```
  ImageTranscription:
    transcript_md: str        # problem statement; LaTeX math, fenced code
    diagram_present: bool     # content not fully capturable as text
    legibility: "ok" | "partial" | "unreadable"
    notes: str | ""           # transcriber caveats shown at review time
  ```

  Prompt contract: transcribe faithfully, do not solve the problem, do not
  paraphrase, preserve code indentation, mark illegible tokens `⟦?⟧`.
- **Cost/limits.** Runs on the ChatGPT subscription; shares its quota with
  interactive Codex use. Fine at interview-prep volume; batch drops of
  hundreds of photos are a reason to add the API-key VLM profile (§8), not
  to raise effort.

## 4. Pipeline integration

- **Job.** New durable job type `image_transcription` on the existing ingest
  queue (`src/learnloop_sidecar/ingest_jobs.py`) so retries/resume/lease
  recovery come for free. Enqueued by `start_ingest`/`start_import_batch`
  when the resolved category is `image`. Per-call Codex app-server startup
  (a few seconds) is why this is a job with visible progress, not a
  synchronous RPC.
- **Extraction run.** The confirmed transcript is persisted as a normal
  `source_extraction_runs` document: `markdown_to_ir` over the transcript,
  one unit, spans grounded in the transcript text. Downstream — outline,
  quick-add scope selection, span-grounded provenance, reading checks —
  works untouched because the image source looks like any tiny markdown
  source after this point. The photo itself is recorded as a
  `DocumentAsset` (`source_document_assets`, media_type `image/*`,
  content_hash = asset hash) so the item can render it.
- **Review before extraction.** The transcript only becomes the extraction
  after the learner confirms the edited text (§5). Until then it lives on
  the job/candidate record — mirrors the synthesis-candidate seam: the
  model's raw output is preserved, mechanical edits happen on top, nothing
  unreviewed reaches the vault.
- **Quick-add, not synthesis.** One photo → `plan_quick_add` with the whole
  (single-unit) scope preselected and a role default of `exam_seed` /
  practice material → `confirm_quick_add` → one proposed practice item via
  the existing priority build batch, enriched per §7 (append-neighborhood
  linking, declared task features, `exam_authentic` tag). A multi-photo drop enqueues N
  independent transcription jobs feeding one review queue; batch synthesis
  over a photo *set* (the v2 exam-seeding workflow) stays future work but
  inherits this capture path.

## 5. UI

- `apps/learnloop-tauri/src/components/useSourceFileDrop.ts`: add the image
  extensions to `SOURCE_EXTENSIONS`; same list in `IngestScreen.tsx`
  `chooseLocalSource()` dialog filters.
- Staged image rows show a thumbnail (served via §2 protocol) instead of the
  document icon; page-range/outline affordances are hidden for images.
- **Transcription review screen** (net-new, small): photo left (zoom/pan),
  editable markdown right with rendered math preview, `notes` and
  `legibility` surfaced as a banner, `diagram_present` rendered as a
  checkbox the learner can override. Confirm → extraction + quick-add plan;
  Discard → job closed, original kept in the store (idempotent re-drop).
- Slice 2 adds: clipboard paste (Tauri clipboard image → temp file → same
  staging path) and a crop step on the staged thumbnail (canvas drag-rect;
  crop happens *before* hashing/storing so the stored original is the
  cropped region).

## 6. Canonical-text principle

The transcript is canonical; the image is provenance. Scheduler, grader,
tutors, and evidence all operate on the text — never on the image. The one
exception: when `diagram_present` is confirmed at review, the item gets the
photo as a visible stimulus attachment (rendered above the prompt during
practice), because a diagram's information genuinely isn't in the text. The
attachment is display-only; grading context still receives only text plus a
one-line "a diagram is shown to the learner" note.

## 7. Enrichment: full items, ladder anchors, retention as a choice

### 7.1 Full practice-item authoring is mandatory

A drop-in problem stored as bare prompt + expected answer would be practice
that produces no measurable evidence: `evidence_facets`/`evidence_weights`
are how a graded attempt reaches the EKF, and `capability`/`task_features`
are what the scheduler and rung gate reason over — all REQUIRED on generated
items already. So the transcription-review confirm does not mint an item
directly; it feeds the same authoring contract every generated item
satisfies, and the enriched item surfaces as a normal proposal (Proposals
screen), keeping the transcription-review screen a fast fidelity check.
Difficulty is declared with `difficulty_source="llm_estimate"` and corrected
empirically from attempt data — the enum already models this lifecycle.

### 7.2 Facet connection rides the append path, not bootstrap

Textbook ingest builds the graph top-down; a drop-in problem is an item
looking for a home in an *existing* graph. Image quick-add therefore routes
enrichment through the append-reconciliation context
(`select_neighborhood`, `services/source_append.py`): link the existing
concepts/LOs the problem exercises, mint new ones only when nothing fits.
Expect the multi-LO case (capability `coordination`, multi-facet evidence
weights) to be the norm for interview problems. In a sparse vault the
proposal flags low-confidence links for review instead of silently growing
a parallel concept tree.

### 7.3 Rung gate carve-out: declared, not targeted

Generated items must hit a target waypoint and the deterministic rung gate
rejects overshoot. A photographed problem *is where it is* in task-feature
space — the model declares `task_features`, and for image-sourced items the
gate records the declaration instead of rejecting off-waypoint. These items
carry an `exam_authentic` provenance tag distinguishing captured ground
truth from synthesized practice.

### 7.4 Ladder anchor

Interview problems arrive at the top of the ladder — far transfer,
`whole_task` span, no scaffolding — which makes them poor first-practice
items but excellent cold-assessment and certification probes. So
`exam_authentic` items are (a) preferred by cold assessment, and (b)
anchors for the existing `rung_variant` machinery: easier siblings are
authored *beneath* them on demand, back-filling the path up to the
authentic exam rung. The photo captures ground truth about what the real
assessment demands; the system generates the approach to it.

### 7.5 Retention as a choice (FSRS)

The point of compiling interesting problems and interview questions is
that *keeping them warm is a deliberate decision, not a side effect*. The
seam already exists: `interval_for_retention(stability, desired_retention)`
(`services/fsrs.py:137`) accepts the knob, but its one call site
(`services/attempts.py:1600`) uses the hardcoded 0.9 default.

- Add a `retention_target` set on the **source set / collection** (not
  per-item config sprawl; an item-level override can come later if ever
  needed), threaded into that call for items belonging to the collection.
- UI: a retention control on the collection with presets — e.g.
  *keep sharp* 0.95 (actively interviewing), *maintain* 0.9 (default),
  *let fade* 0.7 (archive; resurrectable via the existing restoration
  flow). The learner changes it as their situation changes; intervals
  adjust on the next scheduling pass.
- Evidence honesty is preserved: the retention target changes *intervals
  only*. Mastery/EKF evidence and demonstrated-depth records are
  untouched — the system reports predicted retrievability at the chosen
  target rather than pretending one universal retention level.

## 8. Future: OpenAI-API VLM profile (config-only)

When latency, quota, or batch volume justify it:

```toml
[ai.providers.openai_vision]
type = "openai_chat"
base_url = "https://api.openai.com/v1"   # or any OpenAI-compatible VLM host
api_key_env = "OPENAI_API_KEY"
model = "<vision-capable model>"
response_format = "json_object"

[ai.routing]
image_transcription = "openai_vision"
```

Prerequisite code (deliberately deferred from slice 1):
`OpenAIChatProviderClient._chat` (`src/learnloop/ai/openai_chat.py`) is
text-only today; teach it multimodal content parts
(`{"type": "image_url", "image_url": {"url": "data:<media>;base64,..."}}`)
and implement `run_image_transcription` there. Because the task routing and
the getattr-discovery contract already exist from slice 1, this lands as an
isolated provider change — no pipeline or UI edits. The same profile shape
also covers a local vLLM serving Qwen-VL or DeepSeek-OCR (`base_url` swap),
which is the privacy/offline option.

## 9. Marker-pdf VLM boost for hard documents

The same endpoint/key should power marker's existing VLM boost for
especially difficult PDFs (dense math, bad scans). Marker already supports
this via `[ingest.pdf] use_llm / llm_base_url / llm_model /
llm_api_key_env` (`config.py`, `IngestPdfConfig`) — no new code, only a
convention:

- When the `openai_vision` profile is added, mirror it:
  `llm_api_key_env = "OPENAI_API_KEY"`, `llm_base_url`/`llm_model` matching
  the profile (or the local vLLM host). One key, one endpoint, two
  consumers: drop-in image transcription and marker OCR boost.
- Add a per-import "VLM boost" toggle in the ingest UI for documents whose
  extraction health flags `image_only_page`/garbled text — plumbed as an
  override onto the existing `use_llm` config rather than a global flip,
  since the boost is slow and only worth it on hard documents. (The
  extraction-repair flow, `start_extraction_repair`, is the natural place
  to offer "retry with VLM boost".)
- Keep these decoupled at the task level: marker's boost is *page-region
  OCR inside PDF extraction*; `image_transcription` is *whole-problem
  transcription of a drop-in photo*. They share an endpoint, not a code
  path.

## 10. Slices

1. **Vertical MVP** — image source type + originals/serving, `codex_low`
   multimodal transport (`LocalImageInput`), `image_transcription`
   task/job/schema, review screen, quick-add handoff with §7.1–§7.3
   enrichment (append-neighborhood linking, rung-gate carve-out,
   `exam_authentic` tag), diagram-stimulus attachment. Single image,
   pre-cropped, drag-drop + file picker only.
2. **Scheduling role** — cold-assessment preference and rung-variant
   anchoring for `exam_authentic` items (§7.4); collection-level
   `retention_target` threaded into `interval_for_retention` with the
   keep-sharp / maintain / let-fade presets (§7.5). Independent of slice 3
   and small — mostly config plumbing plus one scheduler call site.
3. **Capture comfort** — clipboard paste, in-app crop, multi-photo batch
   drop with a shared review queue, thumbnails polish.
4. **Provider breadth** — `openai_vision` profile + `openai_chat`
   multimodal `_chat`, marker `[ingest.pdf]` mirroring + per-import VLM
   boost toggle in extraction repair.

## 11. Risks / open questions

- **HEIC**: iPhone default format; Rust/browser decoding is spotty. Either
  require JPEG/PNG (phones export JPEG on share) or convert at staging via
  an image crate. Slice 1: reject HEIC with a clear message.
- **Codex app-server cold start** per transcription (~seconds). Acceptable
  as a visible job; if it grates, that is the §8 trigger.
- **Subscription ToS/quota** for programmatic use at higher volumes — same
  standing question as all existing codex-routed tasks, not new to images.
- **One photo, multiple problems** (e.g. a problem-set page): out of scope;
  the transcriber prompt says "transcribe the single primary problem" and
  `notes` flags when more than one is visible.
