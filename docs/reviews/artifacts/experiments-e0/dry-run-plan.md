# E0 dry run `e0_2235492bf452889e`

Harness e0-harness-v1; pins `b1fb4425ca74`; seed 20261021.

**Estimate:** $6.79 expected, $20.36 worst case (every request retried twice) against the $25 cap: fits; allocations fit.

| Category | Expected $ | Worst case $ | Allocation $ | Fits |
|---|---|---|---|---|
| embeddings | 0.0409 | 0.1211 | 2.00 | yes |
| drafting_context | 0.0000 | 0.0000 | 5.00 | yes |
| labels_audits | 4.0422 | 12.1266 | 10.00 | yes |
| answers_verification | 2.7051 | 8.1153 | 8.00 | yes |

| Embedding arm | Model | Documents | Chunks | Requests | Tokens | Expected $ |
|---|---|---|---|---|---|---|
| R1 | qwen/qwen3-embedding-8b | 697 | 697 | 131 | 96,966 | 0.0010 |
| R2 | qwen/qwen3-embedding-8b | 697 | 697 | 131 | 140,502 | 0.0014 |
| R3 | qwen/qwen3-embedding-8b | 697 | 697 | 131 | 218,863 | 0.0022 |
| R4_grouped | pplx-embed-context-v1-4b | 37 | 697 | 121 | 72,463 | 0.0036 |
| R4_singleton | pplx-embed-context-v1-4b | 697 | 697 | 122 | 72,463 | 0.0036 |
| R4_independent | pplx-embed-v1-4b | 697 | 697 | 122 | 72,463 | 0.0022 |
| R5_grouped | voyage-context-4 | 37 | 697 | 121 | 72,463 | 0.0087 |
| R5_singleton | voyage-context-4 | 697 | 697 | 121 | 72,463 | 0.0087 |
| R5_independent | voyage-4-large | 697 | 697 | 121 | 72,463 | 0.0087 |

| LLM role | Model | Billing | Calls | Input tokens | Output tokens | Expected $ |
|---|---|---|---|---|---|---|
| writer | gpt-6-luna | subscription | 12 | 57,436 | 11,520 | 0.0000 |
| context | gpt-6-luna | subscription | 37 | 86,330 | 139,400 | 0.0000 |
| label_a | gpt-6-luna | subscription | 430 | 1,845,616 | 148,264 | 0.0000 |
| label_b | gpt-5.6-sol | subscription | 430 | 1,845,616 | 148,264 | 0.0000 |
| adjudicator | anthropic/claude-sonnet-5.5 | metered | 86 | 1,365,788 | 131,064 | 4.0422 |
| tutor | gpt-5.6-sol | subscription | 362 | 4,730,292 | 217,200 | 0.0000 |
| judge_a | gpt-6-luna | subscription | 362 | 3,065,091 | 108,600 | 0.0000 |
| judge_b | gpt-5.6-sol | subscription | 362 | 3,065,091 | 108,600 | 0.0000 |
| judge_adjudicator | anthropic/claude-sonnet-5.5 | metered | 128 | 1,160,556 | 38,400 | 2.7051 |

**Codex requests:** 3,175 planned against the allowance of 600 (DOES NOT FIT; retries and repairs count too).

**Unverified prices (admission refuses each; the orchestrator fills `price_verified` from the providers' price pages):** none.

Keys: OPENROUTER_API_KEY absent, PERPLEXITY_API_KEY absent, VOYAGE_API_KEY absent
Checks: {"copies_changed": 0, "copy_tree_digests_equal": true, "database_mode": "read_only", "network_calls": 0, "settings_file_read": false}
