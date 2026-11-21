# Structured contracts, preservation steps 1–4

Built on `ai/structured-contracts-1-4` at `3f42da228a`. The production diff is confined to the bootstrap topic predicate in the synthesis controller.

## 1. UX-40 review-route default stays local

`tests/test_section_question_parts.py` pins the exact UTF-8 instruction line and exercises the section job through its writer fake. A grounded, audited `auto_apply` answer lands in the vault. Valid held rows stay pending, the job completes, and the fake records one authoring request per topic. A mixed answer applies only the eligible rows. An empty proposal keeps the existing failed part, message and zero progress. A duplicate refused by the gate stays invalid and fails its part even when another row is valid and held.

The existing full one-topic request digest and checkpoint reuse assertion stay in place. The separate `tests/test_proposal_review_policy.py` cases exercise the route decision directly. The production prompt and policy have an empty diff.

## 2. UX-41 integration and stream guards stay local

`tests/test_chatgpt_plan_runaway.py` pins both first synthesis prompt variants by SHA-256 and checks the actual synthesis request with a null integration. The fake plan stream completes and the caller accepts that answer in one send. A separate answer schema with a required `ok` key still gets the provider's one tool-free schema repair when the key is omitted. `SynthRecipe.integration` is required in the strict outbound schema and defaults to `None` in local parsing, so the omission control uses a field the local parser requires.

The existing transient retry and stream receipt tests remain. Three additional cases pass a predicate that would fail the test if invoked through the public checked-call seam. Whitespace, idle and ceiling cuts propagate their existing transport failures, send once under `single_request`, and never ask for semantic recovery admission. The synthesis prompt, output models and provider have an empty diff.

## 3. UX-42 anonymous create IDs stay local

`tests/test_authoring_create_ids.py` retains the anonymous-ID, named-answer, collision, non-mintable error-type and crash/replay controls. A fresh dispatch and a checkpoint-filling dispatch now demonstrate identical minted and named IDs for the same answer with a later named reservation. The two initial sends have identical bodies. Checkpoint replay preserves those IDs with zero sends, and the fake sees zero corrective requests throughout. The existing occupied-vault control still reaches the first free suffix and keeps it after that ID becomes occupied. The tests now drive the real plan parser with socket-free fake SSE rather than patching the provider's response method. The normalizer and its entry points have an empty diff.

## 4. UX-43 extracts the aggregate predicate

`finish_synthesis_run` calls the named `Predicate` `bootstrap_topic_with_question_plan` on the first merged candidate. The original mode, subject, brief and source-inventory facts still determine whether the build owes a topic. The controller keeps its two-pass loop, discard path, unchanged repeat and second-answer acceptance. The requirement string is metadata on the predicate and never enters a request.

`tests/test_empty_first_build.py` now compares both full requests and checks that a twice-empty run persists the second answer's distinct summary. The narrow adjunct, mapped subject and append still accept a no-topic answer in one send. The rejected-match cases cover both orders of the two conditions, including use of the cached first answer. The two-shard cases prove that one topic across the whole aggregate suffices, and that an empty first aggregate drops both shards and their pass checkpoints before the same requests are sent again. The tests also pin the existing final-pass usage counts.

The empty-then-topic test used the same synthetic one-shard fixture in both captures. Each digest is over a sorted-key JSON serialization of the complete `StructuredRequest`, with `result_model` expanded to its JSON schema.

| Capture | First request SHA-256 | Second request SHA-256 |
|---|---|---|
| Before extraction | `2f9ebc40ad099f46b608d97e5a1ca328212f0f01cb4e26b947ce62408108a8c1` | `2f9ebc40ad099f46b608d97e5a1ca328212f0f01cb4e26b947ce62408108a8c1` |
| After extraction | `2f9ebc40ad099f46b608d97e5a1ca328212f0f01cb4e26b947ce62408108a8c1` | `2f9ebc40ad099f46b608d97e5a1ca328212f0f01cb4e26b947ce62408108a8c1` |

## Verification

`t.sh` and `py.sh` denote the supplied isolated wrappers. The filename selection includes the 18 `test_*.py` files matching `section_question|proposals|runaway|chatgpt_plan|create_id|empty_first_build|source_set_synthesis|structured_contracts`, plus `tests/test_proposal_review_policy.py` and `tests/test_synthesis_tail_golden.py`.

```bash
mapfile -t targets < <(rg --files tests -g 'test_*.py' | rg 'section_question|proposals|runaway|chatgpt_plan|create_id|empty_first_build|source_set_synthesis|structured_contracts' | sort)
t.sh "${targets[@]}" tests/test_proposal_review_policy.py tests/test_synthesis_tail_golden.py -q -n 2 -m 'not arc_close' --tb=line -ra
```

| Command | Last result line |
|---|---|
| `t.sh tests/test_empty_first_build.py -q -n 2 -rP -m 'not arc_close'` before extraction | `15 passed in 10.23s` |
| Same capture after extraction | `15 passed in 9.33s` |
| `t.sh tests/test_authoring_create_ids.py tests/test_chatgpt_plan_runaway.py tests/test_empty_first_build.py tests/test_section_question_parts.py -q -n 2 -m 'not arc_close'` | `80 passed in 40.79s` |
| `t.sh` with the 20 explicit files in the selection above, `-q -n 2 -m 'not arc_close' --tb=line -ra` | `28 failed, 304 passed, 68 errors in 67.67s (0:01:07)` |
| `t.sh tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_public_tip_guards.py tests/test_test_layout.py tests/test_architecture.py -q -n 2 -m 'not arc_close'` | `386 passed in 37.94s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` |
| `git diff --check` | Exit 0, no output |

The review-policy and synthesis golden cases passed in the filename selection. Identity pins and the structure ratchets passed in the guard run. The change adds no private LearnLoop patch site or source-text assertion.

## Unverified

The sandbox denied loopback socket creation with `PermissionError: [Errno 1] Operation not permitted` for all 28 failures and 68 setup errors in the filename selection. Those existing plan integration cases remain unverified here. The changed tests use synthetic vaults and socket-free doubles. Live provider answers, latency, billing, desktop and phone use, the full landing gate and `arc_close` were outside this run. No identity pins or goldens were regenerated.
