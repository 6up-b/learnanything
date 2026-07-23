# Grader-calibration bundles

A bundle ships pre-fitted grader-channel Dirichlet alphas so a new vault does
not relearn a known grader (provider + model revision + prompt + schema) from
the concentration-2 heuristic prior. Import with:

```
learnloop calibration import-bundle calibration_bundles/<name>.yaml --vault <root>
```

Imported models get status `simulation_validated` — they immediately narrow the
certainty interval relative to the heuristic prior, but promotion to
`live_calibrated` still requires the importing vault's own adjudicated anchors
(see `grader_calibration.validate_promotion`).

## Producing a real bundle

Fit alphas from adjudicated grading data in any vault where the same grader
identity has accumulated `calibration_stream_samples` with owner adjudications,
then export the per-cell counts plus the evidence manifest (anchor counts,
held-out Brier/log-loss). Do NOT hand-author alphas: an overconfident bundle
silently narrows every certainty interval downstream. `template.yaml` documents
the format with illustrative (non-evidence) numbers and must not be imported
into a real vault as-is.
