---
title: Privacy and Trust Boundaries
aliases:
  - Egress and Trust
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop/ai
  - src/learnloop/ai/execution.py
  - src/learnloop/db/stores/model_calls.py
  - src/learnloop/substrate/dataset.py
  - src/learnloop/cli/data.py
  - migrations/160_model_call_receipts.sql
  - src/learnloop/content/pipeline
  - src/learnloop/ingest
  - src/learnloop/ops/doctor.py
  - src/learnloop/config
tags:
  - learnloop/architecture
  - learnloop/privacy
  - learnloop/security
  - learnloop/ai
---

# Privacy and Trust Boundaries

LearnLoop is local-first, not “never networked.” Vault state and source artifacts are stored locally; network egress occurs only through an acquisition or configured provider path that the workflow makes visible.

## Trust zones

```mermaid
flowchart LR
    subgraph Local[Local authority]
      V[Vault Markdown/YAML]
      DB[(state.sqlite)]
      IR[Source originals/revisions/IR]
      D[Deterministic domain policy]
    end
    subgraph External[External, untrusted until validated]
      WEB[Source URLs / oEmbed / transcripts]
      MODEL[Configured AI provider]
    end
    WEB -->|captured bytes + metadata| IR
    IR --> D
    D -->|bounded prompt/context| MODEL
    MODEL -->|schema-validated proposal| D
    D -->|semantic gates| V
    D -->|ledgers/receipts/projections| DB
```

External output crosses two boundaries: transport/schema validation and feature semantic validation. It never writes canonical content or learner state directly.

## Source acquisition egress

Local files are read locally. URLs, websites, arXiv, YouTube transcripts/metadata, and other remote sources require network fetches. Acquisition captures immutable bytes/revision identity before later synthesis.

PDF extraction is not always local. Where a PDF or image goes depends on `[ingest.pdf] engine` (default `auto`) and a few keys and settings (`src/learnloop/ingest/extractors/__init__.py` `pdf_extractor_for`, `src/learnloop/ingest/extractors/glm_ocr.py` `selected_backend`, `src/learnloop/content/pipeline/jobs.py` `_document_extractor`; the check is recorded in `docs/reviews/refactor-a4.md`):

- **`auto` with a z.ai key** (`ZAI_API_KEY`, `ZHIPU_API_KEY`, `ZHIPUAI_API_KEY`, or the variable `[ingest.pdf.glm_ocr] api_key_env` names, read from the shell, the vault's `.env` or the machine's `settings.env`, where Settings saves it): GLM-OCR runs on z.ai's hosted `layout_parsing` service, which receives the whole file. It runs only after the learner's one-time OK naming z.ai (the `whole_files_zai` record in `[ai.consent]`; no other OK covers it). Until then a plain import (`learnloop import`, the Ingest screen) reads a PDF here with Marker or pypdf and flags it `glm_ocr_needs_upload_ok`. A scan with no text layer, an image, and an Add from the Library wait for the OK on the book's card instead.
- **`auto` or `glm_ocr` with `[ingest.pdf.glm_ocr] backend = "local"`**: a self-hosted GLM-OCR server at `local_url` gets the selected pages as images, when it answers. No OK is asked, so a `local_url` on another computer receives them without one.
- **`auto` with neither**: local Marker when installed (it may load local model resources), else pypdf. Nothing leaves.
- **`LEARNLOOP_MARKER_PROVIDER=datalab`** (with `DATALAB_API_KEY`; `npm run dev:datalab` sets it): wherever Marker would run, the PDF goes to hosted Datalab Marker instead.
- **`native`**: the whole PDF goes to the `canonical_ingest` chat provider as a file content part. `[ingest.audio] mode = "native"` likewise sends mp3/wav audio to that provider; other audio goes to its separately configured transcription provider. Both native paths require the routed profile to declare the modality in `input_modalities` and cap uploads with `[ingest.native] max_pdf_mb` / `max_audio_mb`. See [[Legacy Configuration Compatibility]] for the retired `[ingest.native]` gates.
- **Marker's `use_llm`** (an extraction repair with "external VLM" and its consent record, or `[ingest.pdf] use_llm` for the one-shot `learnloop ingest`): difficult regions go to the configured OpenAI-compatible vision endpoint.

An Add from the Library sends a whole file to Datalab, the native model or a transcription service only after the separate whole-file OK (`whole_files`). A plain import whose engine was chosen explicitly asks nothing more; the Ingest screen says, beside a `native` choice, that the whole PDF goes to the ingest model. An extraction repair the learner OK'd as local never leaves this computer: it passes over z.ai, GLM-OCR servers on other computers, Datalab and the native model. Once a PDF is extracted, passages of its text go to the connected AI in bounded contexts under the connection's OK (see AI egress below).

## AI egress

Every feature resolves a named route through [[AI Architecture#Resolution path]]. The operation builds a bounded context rather than handing a provider the whole vault. Provider/profile/model identity and token usage are recorded in run provenance. Manual mode sends nothing.

## Prompts and responses stored locally

Model calls made under a model-call observer (desktop sidecar RPCs, durable ingest jobs, and CLI practice grading) write a [[Reference/Database/Tables/model_call_receipts|model_call_receipts]] row when the call starts. The row keeps the prompt text of the top-level call (`input_text`), its output schema, and the returned text (`output_text`), alongside provider, model, endpoint, status and usage. Prompts routinely contain learner answers and source excerpts, so `state.sqlite` holds that text for every observed call; it is a `RECEIPT` table and is never cleared by a rebuild.

## Dataset export

`learnloop dataset-export OUTPUT` copies learner data out of the vault. The output directory must not already exist. It contains:

- `snapshot.sqlite`, a complete SQLite backup of the vault database (every table, not a selection);
- one JSONL file for every `RAW_LEDGER` and `RECEIPT` table, which includes `model_call_receipts` prompt and response text, `raw_grade_events`, `practice_attempts`, and `practice_item_snapshots` (full item text);
- JSONL files for the captured workflow tables `proposed_patches`, `proposed_patch_items`, `synthesis_runs`, `model_work_checkpoints`, `ingest_batches`, `ingest_jobs`, and `attempt_completion_work`;
- `outcome_contract.jsonl` and `split_assignments.jsonl`;
- `manifest.json`, with the hashes of the snapshot and of every artifact.

Source originals are referenced by hash and not copied. Every artifact is fsynced, and the manifest is written last by atomic rename, so its presence marks a complete export; a failed export removes the directory it created. Treat an export as containing everything the learner typed and every prompt sent to a provider. See [[Collection and Dataset Contract]].

## Secrets and machine-specific values

API keys are referenced by environment-variable names, not stored as plaintext vault values. Machine paths and global defaults belong in environment/global settings layers described by [[Environment and Machine Settings]]. A vault may inherit AI settings when first created, but existing vaults are not overwritten.

## Diagnostics

Plain doctor is physically database-read-only and does not probe providers. A provider diagnostic happens only when explicitly requested by an AI workflow. This keeps “inspect my vault” from becoming an unexpected mutation or egress event.

## Instruction and evidence trust

Reader/tutor output may reveal source content and therefore records familiarity/exposure; it cannot become ability evidence merely because a model supplied it. Assessment output is treated as a proposal and checked against the frozen contract. See [[Evidence and Measurement]] and [[Reader Tutor and Teach-Back]].

## Modification guidance

- Document every new egress path, required consent, payload scope, retry, and provenance.
- Keep secrets out of TOML/Markdown examples; reference environment variables.
- Make offline/manual behavior explicit.
- Add a no-egress test for unsupported capability/fallback cases.
- Never add a provider call to plain doctor or a read-only data inspection path.
- A new table classified `RAW_LEDGER` or `RECEIPT` is exported by `dataset-export` automatically; decide whether its contents belong in an export before choosing the role.

