# Changelog

## Grade-channel discount revision (P1/P2/P4)

Fixes two cold-channel artifacts: a perfect score could *lower* displayed
mastery on easy items, and Demonstrated in the knowledge field stayed at 0
because certification credit was double-discounted. No new migrations; pinned
interpretations keep their persisted LCBs.

- **P1 — mean-preserving prediction lane.** The mastery EKF keeps the raw
  rubric fraction as its observation; the calibrated grade channel contributes
  only `Var[s|emission]` to measurement noise. Channel doubt now widens R
  instead of shrinking y toward the prior (which capped a perfect AI-graded
  answer at E[s|success] and inverted the update direction whenever predicted
  correctness exceeded that ceiling).
- **P2 — epistemic-only certification discount.** `EffectiveObservation`
  multiplies mass by `certainty_lcb / certainty` instead of the raw LCB. The
  posterior split (`E[s|emission]`) already prices the aleatoric hedge once;
  the mass factor now carries only ensemble (model) doubt, tends to 1 as
  calibration data accumulates, and stays 1 for deterministic/adjudicated
  grades. Uniform/quarantined/missing interpretations still bank zero.
- **P4 — channel knobs are fitted parameters.** Heuristic prior reliability
  floor (default 0.92, was a bare 0.80) and the certainty-LCB ensemble
  quantile (default 0.25, was 0.10) resolve from the `fitted_parameters`
  store (scope `grader_channel_prior`). Heuristic seeding is re-run
  content-addressed on every model resolution and global-prior resolution is
  latest-wins, so a retuned prior reaches already-seeded vaults.

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
