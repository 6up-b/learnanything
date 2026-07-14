# Changelog

## ING M3.5 — Source ingestion v2-lite

The first shippable slice of the source-ingestion v2 redesign. It wires the new
extraction/queue/selection stack (ING M1–M3) into the existing single-source
synthesis pipeline, so users get better ingestion today while the new knowledge
model (KM1/KM2) lands. No new migrations.

- **Better extraction.** Sources are extracted once into a structured Document
  IR (blocks, units, assets, extraction-health flags) with version-pinned
  caching, instead of a one-shot markdown flatten. Difficult PDF pages can be
  improved with a consent-gated, page-range extraction repair.
- **Durable, resumable queue.** Ingestion runs as durable batches/jobs that
  survive restarts, with a checkpoint ladder, per-call token/usage accounting,
  and cancel/resume. The single-source Ingest flow now runs `import` (extract to
  IR) → `legacy_ingest` (synthesis) as one dependent batch — extract once, reuse
  everywhere.
- **Source library + build preview.** Imported sources appear as cards with
  health and token progress; outline, acquisition preview, and a per-stage build
  plan show costs before any pedagogical LLM call.
- **Unit selection.** Choose which chapters/sections feed synthesis; the
  selection survives re-extraction and is honored end to end.
- **IR-driven synthesis.** Legacy synthesis now builds its chunk context from the
  IR's deterministic display rendering (`render_ir_markdown`), respecting the
  persisted unit selection (selected units only). Sources without an IR (legacy
  call paths, non-imported) keep the previous behavior byte-for-byte.
