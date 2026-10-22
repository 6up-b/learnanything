# E0 dry run `e0_dec5776aa73cdd5a`

Harness e0-harness-v2; pins `0ca2618ddc40`; seed 20261021.

**Estimate:** $37.84 expected, $113.53 worst case (every request retried twice) against the $40 cap: fits; allocations fit.

| Category | Expected $ | Worst case $ | Allocation $ | Fits |
|---|---|---|---|---|
| embeddings | 0.0409 | 0.1211 | 0.50 | yes |
| drafting_context | 0.5069 | 1.5207 | 1.50 | yes |
| labels_audits | 23.6220 | 70.8660 | 24.00 | yes |
| answers_verification | 13.6745 | 41.0234 | 14.00 | yes |

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
| writer | claude-sonnet-5-5 | metered | 12 | 57,436 | 29,520 | 0.4101 |
| context | claude-haiku-5-5 | metered | 37 | 86,330 | 176,400 | 0.0968 |
| label_a | claude-haiku-5-5 | metered | 430 | 1,845,616 | 578,264 | 0.4737 |
| label_b | claude-sonnet-5-5 | metered | 430 | 1,845,616 | 793,264 | 11.6239 |
| adjudicator | claude-opus-5-5 | metered | 86 | 1,365,788 | 303,064 | 11.5244 |
| tutor | claude-haiku-5-5 | metered | 362 | 4,730,292 | 579,200 | 0.7626 |
| judge_a | claude-haiku-5-5 | metered | 362 | 3,065,091 | 470,600 | 0.5418 |
| judge_b | claude-haiku-5-5 | metered | 362 | 3,065,091 | 470,600 | 0.5418 |
| judge_adjudicator | claude-opus-5-5 | metered | 128 | 1,160,556 | 294,400 | 10.5302 |

| System-arm LLM requests | Vault | Model | Requests | Input tokens | Output tokens | Expected $ | Price |
|---|---|---|---|---|---|---|---|
| R0_llm | vault_885a8c06e4 | anthropic/claude-haiku-5.5 | 252 | 756,000 | 403,200 | 0.2772 | verified |
| R1_service_llm | vault_885a8c06e4 | anthropic/claude-haiku-5.5 | 378 | 1,134,000 | 604,800 | 0.4158 | verified |
| R0_llm | vault_83d3a40c75 | anthropic/claude-haiku-5.5 | 220 | 660,000 | 352,000 | 0.2420 | verified |
| R1_service_llm | vault_83d3a40c75 | anthropic/claude-haiku-5.5 | 330 | 990,000 | 528,000 | 0.3630 | verified |

**Codex requests:** 0 planned; the paid ledger's Codex allowance is 0 (E0 makes no Codex call: fits).

**Unverified prices (admission refuses each; the orchestrator fills `price_verified` from the providers' price pages):** none.

Keys: ANTHROPIC_API_KEY absent, OPENROUTER_API_KEY absent, PERPLEXITY_API_KEY absent, VOYAGE_API_KEY absent
Checks: {"copies_changed": 0, "copy_tree_digests_equal": true, "database_mode": "read_only", "network_calls": 0, "settings_file_read": false}
