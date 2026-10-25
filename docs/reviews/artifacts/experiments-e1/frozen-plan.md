# E1 plan e1_eaa8d20e4af40e3f (frozen)

Source: import; E0 run e0_e6a077cd391c5421 (complete: True).
Model: perplexity-ai/pplx-embed-v2-context-9b-preview @ e2c06a77, bf16, 33.6 GB on disk.

| Vault | Units | Windows | Grouped tokens | Singleton tokens | Queries | Labelled questions |
|---|---|---|---|---|---|---|
| linear_algebra-20261021 | 362 | 10 | 26,137 | 26,137 | 63 | 47 |
| probability-20261021 | 335 | 27 | 33,120 | 33,120 | 55 | 39 |

GPU: expected 0.33 h, worst case 0.65 h of 4 h ({'load_s': 600.0, 'smoke_s': 180.0, 'profile_s': 43.0, 'documents_s': 118.5, 'queries_s': 236.0}).
Money: expected $2.94, worst case $10.21 against $5.00 left of $5.00 (fits: True).
Priority past the cap: primary development questions first, then logged, then the other development strata; past the cap the rest stays unknown (pool-relative completeness, reported).

Keys: {'ANTHROPIC_API_KEY': 'absent', 'VOYAGE_API_KEY': 'absent'}.
