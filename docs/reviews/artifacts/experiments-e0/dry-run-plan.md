# E0 dry run `e0_65d691edcd7bf7d7`

Harness e0-harness-v1; pins `bbcce15ed6cd`; seed 20261021.

**Estimate:** $8.71 expected, $26.13 worst case (every request retried twice) against the $25 cap: fits; allocations fit.

| Category | Expected $ | Worst case $ | Allocation $ | Fits |
|---|---|---|---|---|
| embeddings | 0.1154 | 0.3404 | 2.00 | yes |
| drafting_context | 0.0000 | 0.0000 | 5.00 | yes |
| labels_audits | 5.2086 | 15.6257 | 10.00 | yes |
| answers_verification | 3.3871 | 10.1613 | 8.00 | yes |

| Embedding arm | Model | Documents | Chunks | Requests | Tokens | Expected $ |
|---|---|---|---|---|---|---|
| R1 | qwen/qwen3-embedding-8b | 697 | 697 | 14 | 87,812 | 0.0026 |
| R2 | qwen/qwen3-embedding-8b | 697 | 697 | 14 | 131,349 | 0.0039 |
| R3 | qwen/qwen3-embedding-8b | 697 | 697 | 14 | 209,748 | 0.0063 |
| R4_grouped | pplx-embed-context-v1-4b | 37 | 697 | 4 | 66,438 | 0.0133 |
| R4_singleton | pplx-embed-context-v1-4b | 697 | 697 | 5 | 66,438 | 0.0133 |
| R4_independent | pplx-embed-v1-4b | 697 | 697 | 5 | 66,438 | 0.0133 |
| R5_grouped | voyage-context-4 | 37 | 697 | 4 | 66,438 | 0.0199 |
| R5_singleton | voyage-context-4 | 697 | 697 | 4 | 66,438 | 0.0199 |
| R5_independent | voyage-4-large | 697 | 697 | 4 | 66,438 | 0.0199 |

| LLM role | Model | Billing | Calls | Input tokens | Output tokens | Expected $ |
|---|---|---|---|---|---|---|
| writer | gpt-6-luna | subscription | 12 | 57,427 | 11,520 | 0.0000 |
| context | gpt-6-luna | subscription | 37 | 86,330 | 139,400 | 0.0000 |
| label_a | gpt-6-luna | subscription | 404 | 1,725,770 | 153,924 | 0.0000 |
| label_b | gpt-5.6-sol | subscription | 404 | 1,725,770 | 153,924 | 0.0000 |
| adjudicator | anthropic/claude-sonnet-5.5 | metered | 101 | 1,597,904 | 153,924 | 5.2086 |
| tutor | gpt-5.6-sol | subscription | 407 | 5,368,932 | 244,200 | 0.0000 |
| judge_a | gpt-6-luna | subscription | 407 | 3,496,732 | 122,100 | 0.0000 |
| judge_b | gpt-5.6-sol | subscription | 407 | 3,496,732 | 122,100 | 0.0000 |
| judge_adjudicator | anthropic/claude-sonnet-5.5 | metered | 144 | 1,323,590 | 43,200 | 3.3871 |

Keys: OPENROUTER_API_KEY absent, PERPLEXITY_API_KEY absent, VOYAGE_API_KEY absent
Checks: {"copies_changed": 0, "copy_tree_digests_equal": true, "database_mode": "read_only", "network_calls": 0, "settings_file_read": false}
