# Stage 0–5 original-spec audit

**Audit date:** 2026-07-26  
**Plan:** `implementation_plan_v1.md`  
**Authorities:** `spec_causal_attribution_v1.md`,
`spec_diagnostic_augmentation_v1.md`, `spec_measurement_efficiency_v1.md`

## Verdict

Stages 0–4 are implemented and wired after the corrections below. Stage 5 is
implemented as planned, but it is **not fully compliant with the original
measurement/augmentation specs**:

1. The §3.0 persona gate has no augmentation B2 blinded persona-vs-real
   validation. Every persisted result correctly says
   `persona_realism_validated: false`; the original spec says such verdicts do
   not count.
2. The D2 facet-mint gate uses exclusive normalized error signatures as a
   structural authorability proxy. It does not author and grade a
   discriminating item through §3.0's shared planted-persona harness.

These are now marked as open original-spec obligations in
`implementation_plan_v1.md` and surfaced as warnings in the Tauri Maintain
screen. They are not silently represented as completed gates.

## Stage results

| Stage | Verdict | Evidence / correction |
|---|---|---|
| 0 | Complete | D3 ingest gate, capability-cell mapping, scoped coverage, exam conjunctive coverage, quality gates, strict-schema plumbing, and the causal principle amendment are present with regression coverage. |
| 1 | Complete | Repair-key taxonomy, token capture, missing-vocabulary capture/reporting, and surfaced-belief corrections are wired. Authoring-side missing-vocabulary notes now carry the actual authoring run/prompt/model/provider plus decision/repair policy versions. |
| 2 | Complete after correction | Commissioning, review ladder, promotion arms, and manipulation auditors are wired. The default blind-bundle generator previously consumed observation-conditioned `postdictive_claims`, violating causal §5.1. It now consumes only typed `target_ref` plus the fresh item/rubric contract; postdictive claims are excluded from the safe generator payload and cannot affect discrimination. |
| 3 | Complete | Static contract reachability, measured/inferred/claimed/unknown labels, contract-frontier coverage, and published measurement rank are implemented and visible. |
| 4 | Complete after integration correction | The frozen B5 scoreboard, token/probe/harmful-write metrics, and delayed held-out cold-probe producer/report are implemented. The Tauri live submission path now schedules an eligible certificate immediately; app load self-heals older certificates; replay and the explicit CLI scheduler retain their prior semantics. |
| 5.1 | Complete | Contract commissioning drives authoring at the contract capability and reports deferred coordination cells explicitly. |
| 5.2 | Complete | Coordination-only D3 backfill, dry-run diffs, affected-LO replay, and one content-addressed learner recalibration boundary are implemented. Tauri exposes diff review plus an explicit-confirmation apply action. |
| 5.3 | Partial | Gate mechanics and typed audit outcomes are live on generation routes, but B2 persona realism is not validated. |
| 5.4 | Partial | Typed MINT/ALIAS/ABSTAIN decisions and alias rewiring are live at ingest, but the original shared-harness execution is still absent. |

## Tauri and sidecar coverage

The Maintain screen now consumes one authoritative sidecar health payload rather
than reimplementing metrics in TypeScript. It shows:

- the ordered B5 scoreboard with explicit unavailable arms and denominators;
- contract reachability and the commissioning queue;
- delayed cold-probe coverage and scheduling;
- missing-vocabulary capture and uncaptured-abstention alarms;
- causal-lane fill/abstention health;
- persona-gate validity status and precision availability;
- the D2 structural-proxy limitation and current mint audit;
- D3 coordination-backfill diffs and confirmed application;
- causal probe candidates, blind-separability state, and the
  candidate → registered → reviewed → active/rejected review ladder.

Existing learner surfaces also render measurement-state labels, measurement
rank, latency capture, and surfaced-belief withdrawals.

## Remaining work required for a fully green original-spec verdict

1. Implement augmentation B2's blinded persona-vs-real matcher and make §3.0
   gate authority conditional on its validity result.
2. Replace D2's structural authorability proxy with an actual authored
   discriminating item graded through the shared §3.0 planted-persona harness,
   preserving the existing typed failure and alias/review records.

Those obligations belong to later plan stages today; completing them would be a
scope change, not a missing Tauri binding.

The blind-input correction is versioned as
`observation_free_hypothesis_target_v2`. Candidates minted without that stamp
remain visible for audit but cannot be registered, activated, or served; a
commissioning sweep withdraws an older active/pending candidate through the
append-only review-event log before replacing it.
