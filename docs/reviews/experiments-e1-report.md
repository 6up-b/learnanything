# E1 report e1_eaa8d20e4af40e3f (incomplete)

E0 run: e0_e6a077cd391c5421. Decision: **no_verdict** (linear_algebra-20261021: supplementary κ below 0.6; probability-20261021: supplementary κ below 0.6).
Production adoption: not_authorized_by_e1.

## Local run

Processes: 2 (['failed', 'complete']); wall 52.786 s; GPU meter {'by_status': {'exited': 2, 'failed': 1}, 'cap_hours': 4.0, 'processes': 3, 'remaining_hours': 3.9721, 'used_hours': 0.0279}.
Load: {'attention': 'sdpa', 'capability': [12, 0], 'cuda': '13.0', 'device': 'NVIDIA GeForce RTX 5090', 'device_after_load': {'allocated': 16852580352, 'free': 14821031936, 'max_allocated': 16874373120, 'max_reserved': 16894656512, 'reserved': 16894656512, 'total': 33743044608}, 'fp32_modules': {'contextual_projection': True}, 'kernel_messages': ['`causal_conv1d_fn` is falling back to its reference PyTorch implementation because `causal_conv1d` is not installed. This is correct but much slower; install `causal_conv1d` for the optimized kernel.', '`chunk_gated_delta_rule` is falling back to its reference PyTorch implementation because `flash-linear-attention` is not installed. This is correct but much slower; install `flash-linear-attention` fo'], 'load_s': 24.711, 'parameter_dtypes': {'bfloat16': 8392695024, 'float32': 8388608}, 'precision': 'bf16', 'repairs': {'fp32_restore': {'contextual_projection': 'restored_from_checkpoint'}, 'page_cache_dropped_files': 8, 'tokenizer': 'loaded from the model directory (remote getter needs config._commit_hash)'}, 'torch': '2.14.0+cu130', 'transformers': '5.18.0'}.
Smoke: {'all_ok': True, 'context_sensitive': {'cosines': {'a_vs_alone': 0.924608, 'a_vs_b': 0.747828, 'b_vs_alone': 0.763148}, 'ok': True}, 'decoding': {'ok': True, 'problems': [], 'unnormalized_norm_min': 1692.715}, 'deterministic': {'ok': True}, 'dims_and_order': {'ok': True, 'shapes': [[3, 2048], [3, 2048], [1, 2048]]}, 'finite_nonzero': {'ok': True}, 'methods_separate': {'ok': True, 'query_vs_document_cos': 0.702469}, 'no_truncation': {'limit': 8192, 'ok': True, 'probe_tokens': 13233, 'smoke_tokens': [58, 55, 23]}, 'padding_batch_invariance': {'document_min_cos': 0.99991, 'ok': True, 'query_cos': 0.999913, 'tolerance': 0.995}}.
Profile: {'2048': {'device_max_allocated': 17210045440, 'device_max_reserved': 17255366656, 'latencies_s': [0.1493, 0.1502, 0.1494], 'oom': False, 'tokens': 1351}, '4096': {'device_max_allocated': 17604403200, 'device_max_reserved': 17695768576, 'latencies_s': [0.3098, 0.3107, 0.3136], 'oom': False, 'tokens': 2926}, '8192': {'device_max_allocated': 18289289728, 'device_max_reserved': 18429771776, 'latencies_s': [0.6496, 0.6558, 0.6589], 'oom': False, 'tokens': 5603}}.
Peaks: {'device_reserved_max': 18429771776, 'gpu_used_mib_max': 18216, 'host_available_min': 20745449472, 'rss_anon_max': 1964744704, 'rss_max': 12998668288, 'samples': 51, 'scope_current_max': 12884901888, 'scope_peak': 12884901888}; device {'allocated': 16852580352, 'free': 13283819520, 'max_allocated': 18289289728, 'max_reserved': 18429771776, 'reserved': 18429771776, 'total': 33743044608}; unload {'allocated_after': 0, 'complete': True, 'cublas_workspaces_cleared': True, 'reserved_after': 0}.
Documents {'encoded': 734, 'latency_s': {'n': 734, 'p50': 0.0187, 'p95': 0.046}, 'tokens': 87179}; queries {'batch_one_latency_s': {'n': 116, 'p50': 0.0182, 'p95': 0.0272}, 'encoded': 116}.

## Comparisons (primary development slice, paired, family-clustered)

- context_gain_v2: +0.034 [-0.069, +0.182], n=58, families=5
- v2_vs_R4: +0.034 [-0.037, +0.111], n=58, families=5
- v2_vs_R5: -0.017 [-0.074, +0.037], n=58, families=5
- v2_vs_best_frozen: -0.017 [-0.074, +0.037], n=58, families=5
- v2_vs_best_frozen:logged: +0.222 [+0.000, +0.333], n=9, families=3 (exploratory)
- v2_vs_one_model: +0.000 [-0.037, +0.037], n=58, families=5

v2 arm selected on the same slice: V2_grouped.

## linear_algebra-20261021

Finalists: {'R4': 'R4_grouped', 'R5': 'R5_grouped', 'one_model': 'R1'}; best frozen: R1; replay reproduced E0: True; E0 S1: labels_ok.

| Arm | CE@10 | Support@10 | Answer@10 | nDCG@10 | MRR | Unknown | Scored |
|---|---|---|---|---|---|---|---|
| R1 | 0.828 | 0.904 | 0.988 | 0.713 | 0.907 | 0.000 | 29/30 |
| R2 | 0.724 | 0.881 | 0.988 | 0.683 | 0.865 | 0.000 | 29/30 |
| R3 | 0.759 | 0.917 | 0.952 | 0.701 | 0.908 | 0.000 | 29/30 |
| R4_grouped | 0.759 | 0.889 | 0.952 | 0.714 | 0.950 | 0.000 | 29/30 |
| R4_independent | 0.724 | 0.855 | 0.863 | 0.643 | 0.867 | 0.000 | 29/30 |
| R4_singleton | 0.724 | 0.852 | 0.845 | 0.642 | 0.900 | 0.000 | 29/30 |
| R5_grouped | 0.828 | 0.909 | 0.946 | 0.700 | 0.863 | 0.000 | 29/30 |
| R5_independent | 0.793 | 0.917 | 0.916 | 0.728 | 0.925 | 0.000 | 29/30 |
| R5_singleton | 0.793 | 0.910 | 0.970 | 0.735 | 0.917 | 0.000 | 29/30 |
| V2_grouped | 0.862 | 0.939 | 0.911 | 0.764 | 0.955 | 0.000 | 29/30 |
| V2_singleton | 0.724 | 0.889 | 0.970 | 0.676 | 0.933 | 0.000 | 29/30 |

Supplementary labels: {'agreement': {'adjudicated': 12, 'agreement': {'categories': ['unrelated', 'background', 'helpful', 'required'], 'confusion': [[26, 4, 2, 0], [0, 2, 0, 0], [0, 0, 0, 1], [0, 0, 0, 0]], 'kappa': 0.3536, 'n': 35, 'observed_agreement': 0.8, 'weighted_kappa': 0.4112}, 'unresolved': 1}, 'audits': {'done': 12, 'mandatory_missing': 0, 'planned': 12, 'sampled_missing': 0}, 'counts': {'failed': 0, 'missing': 0, 'new_candidates': 35, 'questions_with_new': 17, 'stopped': None}}; merged: {'labels_added': 28, 'made_answerable': 0, 'sets_added': 1, 'unresolved_left_unknown': 1}.

## probability-20261021

Finalists: {'R4': 'R4_singleton', 'R5': 'R5_grouped', 'one_model': 'R1'}; best frozen: R5_grouped; replay reproduced E0: True; E0 S1: labels_ok.

| Arm | CE@10 | Support@10 | Answer@10 | nDCG@10 | MRR | Unknown | Scored |
|---|---|---|---|---|---|---|---|
| R1 | 0.828 | 0.914 | 0.962 | 0.752 | 0.967 | 0.000 | 29/30 |
| R2 | 0.724 | 0.856 | 0.962 | 0.695 | 0.944 | 0.000 | 29/30 |
| R3 | 0.759 | 0.885 | 0.904 | 0.746 | 0.950 | 0.000 | 29/30 |
| R4_grouped | 0.690 | 0.828 | 0.865 | 0.694 | 0.903 | 0.000 | 29/30 |
| R4_independent | 0.793 | 0.874 | 0.865 | 0.676 | 0.967 | 0.000 | 29/30 |
| R4_singleton | 0.828 | 0.914 | 0.942 | 0.691 | 0.967 | 0.000 | 29/30 |
| R5_grouped | 0.862 | 0.948 | 1.000 | 0.786 | 0.975 | 0.000 | 29/30 |
| R5_independent | 0.828 | 0.940 | 0.981 | 0.768 | 0.950 | 0.000 | 29/30 |
| R5_singleton | 0.862 | 0.951 | 1.000 | 0.790 | 0.942 | 0.000 | 29/30 |
| V2_grouped | 0.793 | 0.914 | 0.942 | 0.742 | 0.913 | 0.000 | 29/30 |
| V2_singleton | 0.862 | 0.948 | 0.962 | 0.757 | 0.967 | 0.000 | 29/30 |

Supplementary labels: {'agreement': {'adjudicated': 12, 'agreement': {'categories': ['unrelated', 'background', 'helpful', 'required'], 'confusion': [[28, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]], 'kappa': 0.5753, 'n': 31, 'observed_agreement': 0.9355, 'weighted_kappa': 0.6437}, 'unresolved': 0}, 'audits': {'done': 12, 'mandatory_missing': 0, 'planned': 12, 'sampled_missing': 0}, 'counts': {'failed': 0, 'missing': 0, 'new_candidates': 31, 'questions_with_new': 18, 'stopped': None}}; merged: {'labels_added': 31, 'made_answerable': 0, 'sets_added': 0, 'unresolved_left_unknown': 0}.

Spend: {'by_category': {'labels_audits': '0.718624'}, 'committed_usd': '0.718624', 'entries': 98, 'file': 'e1_eaa8d20e4af40e3f.ledger', 'superseded': None}.
