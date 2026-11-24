# K9.13 posterior replay and K9.17 successor design

Branch `refactor/k9-13-17`, tip `86f29b0d390ed2ecdbb0347d98ccb1175ac52728`. Working tree for the orchestrator to commit.

## Status note for the orchestrator

| Row | State | Grounds |
| --- | --- | --- |
| G4 | Closed, skipped | Owner, 2026-11-23, “don't unify; close G4”. The upgraded G3 copy had four paired answers. Both channels excluded the same three exposed answers. All five cards mapped every locked cause to the same slot. The posterior stayed at its prior and no preregistered match closed a factor. |
| K9.13 | Implemented and verified on synthetic histories, ready to land | Five-field frozen `EpisodeEvidence`, ordered gather and pure `fold_posterior`. The owner-copy P-shadow check remains with the orchestrator. |
| K9.17 | Design only, queued as its own persisted-meaning successor | Proposed `mvp-0.71` after the in-flight tags. Ledger K9-3 remains open. Storage for a superseding episode observation and the owner-copy comparison require a separate landing. |

The decision follows the November 20 rerun at the end of the [G3 record](refactor-g3.md) and the independent-successor branch of the [K9 strategy, §4.6](k9-diagnosis-strategy-2026-11-14.md#46-inside-arc-g-what-k9-hands-g1-g3-and-g4).

## K9.13 read and fold boundary

The public `episode_posterior` still resolves the locked hypothesis set only when needed and returns `None` for an absent or empty set. The gather reads the first intervention, effective observations (including the exposure reread), learning-object attempts in repository order, then held IDs including the in-flight holds. Its loop keeps the old conditional reads of presentation status, frozen card and slot map, stored outcome or legacy classification inputs, and incidental item likelihoods. Every read is determined by the episode, attempt or recorded observation. The only dependence on the running posterior was the marginal for the next Bayes update.

The gather collects only admitted likelihoods and weights, counts observed presentations and retains their completion candidates and the held set. The fold copies the locked prior, uses the running posterior as the marginal reference at every update, excludes held candidates from the qualifying count, and computes final entropy. Incidental evidence can move belief without adding an observation. An inert probe still counts as answered. Production diff +51/−23 lines (net +28), plus 43 lines of literal tests.

## Proof

All Python, pytest and lint commands used the checkout venv and the requested empty environment. In the table, `T` expands to `python -m pytest -q -n 1 -p no:cacheprovider`. Pytest commands ran sequentially. Scratch inputs were synthetic.

| Command | Result |
| --- | --- |
| `T tests/test_diagnosis_journey_golden.py` before editing | 21 passed in 13.05s |
| `T tests/test_episode_posterior_fold.py` against the untouched source | 2 failed in 1.22s, both at the missing `EpisodeEvidence` interface |
| `T tests/test_episode_posterior_fold.py tests/test_diagnosis_journey_golden.py tests/test_identity_pins.py tests/test_probe_episodes.py tests/test_characterization_probe_regrade.py tests/test_held_grade_evidence.py tests/test_structure_ratchets.py` after editing | 474 passed in 44.36s |
| `T tests/test_evidence_reading_successor.py` | 54 passed in 12.66s |
| `python - < .codex-scratch/equivalence.py` | 7 identical helper ASTs. 30 exact return values and ordered SQL traces matched, 218 statements per implementation |
| `python - < .codex-scratch/shadow.py` before and after | Both fixture reports matched byte for byte, including source hashes and live and rebuilt episode posteriors |
| `ruff check src/learnloop/diagnosis/probe_episodes.py tests/test_episode_posterior_fold.py` | All checks passed |
| `lint-imports --no-cache` | Contracts: 54 kept, 0 broken |
| `python docs/learnloop-architecture-vault/_scripts/validate_vault.py` | Passed, 2,538 notes |
| `python docs/learnloop-architecture-vault/_scripts/module_validate.py` | Passed, 1,394/1,394 source modules |
| `python docs/learnloop-architecture-vault/_scripts/desktop_validate.py` | One reproducibility error, stale `Reference/_generated.md` |
| `python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py` | One stale generated source-line citation for `probe.episode.hinted_evidence_weight` in `Config - probe` |
| `git diff --check` | Passed |

**Assertions.** All existing assertions stand. The first new test checks the locked set's identity, the untouched ½–½ prior, the exact ⅝–⅜ posterior, its entropy, one qualifying probe and three observations. The second step uses weight ½, so using the opening prior again or reversing the evidence changes the answer. The second test checks exact prior and posterior equality, zero qualifying probes and one answered probe when the update sequence is empty. Both the journey golden and identity fixture match their HEAD bytes.

**Equivalence method.** Compile the original `episode_posterior` from `git show HEAD:src/learnloop/diagnosis/probe_episodes.py` into the module's globals. Compare it with the public working-tree function on the same read-only synthetic DB, collecting the SQLite trace on a pinned connection for each call. Use the held-release and regrade journey databases and one mixed history with a presented probe plus hinted, ordinary and exam attempts. For each, try the default set, the supplied lock, and an explicitly empty set, with no in-flight hold, all attempts held and each individually held. Compare the entire returned dataclass or `None` and every SQL statement in order. The helper ASTs compared were the Bayes step, entropy, both likelihood readers, effective episode observations, the intervention boundary and the hypothesis-set reader. The first setup attempt used a synthetic item that disallowed hinted attempts. The completed comparison used the fixture's ordinary item, which supports all three incidental types.

**Shadow method.** Build `tests.diagnosis_journey_helpers.probe_case` once each for `held_release` and `regrade` at `mvp-0.68`. Before and after the source edit, run `shadow_rebuild` on those same databases with an observer returning the full episode posterior on each side. Compare both posteriors, all mastery/facet/schedule diff rows, both schedule snapshots and the source DB hash across source revisions. Each posterior also agreed live versus rebuilt. The held-release fixture calls the low-level adjudication writer directly, and its shadow already showed one changed mastery row at HEAD. That exact row recurred after the edit. The regrade fixture had zero differences, and neither fixture had a facet or schedule delta. Owner copies were outside the sandbox. The orchestrator's same-tag pre/post shadow on backup-API copies remains outstanding.

## K9.17 design and stop decision

**Persisted meaning changes.** A held submission consumes the presentation and records a zero-weight observation with no outcome. Its release clears the current hold but leaves that receipt inert. An assessed regrade can publish a replacement grade interpretation while the episode still reads the submission's instrument outcome. Substituting the released or regraded outcome changes the ordered posterior on the same history. `probe_completion.persist_episode_beliefs` writes its misconception means, variances and surprise to `learner_state_beliefs`. Later probe selections, qualifying counts and stopping decisions can also change. The playbook therefore requires a new tag with historical replay. [Algorithm-change playbook](../algorithm-change-playbook.md)

1. On a validating release or regrade, derive a superseding episode observation keyed to the original attempt, presentation and current grading epoch (`grading_epochs.current_epoch`). Use the epoch's frozen assessment contract and admissible criterion evidence, the presentation's frozen card and slot map, and the original answer's exposure and contamination. Preserve evidence-share and assessable-trace caps. A still-held or exposed response contributes zero. Publish each revision atomically and idempotently with the epoch. A retry or concurrent regrade must leave one effective reading per attempt.
2. Replay the latest applicable revision **once, at the original attempt position**, then fold the later evidence against the revised running posterior. As-of readers can see only revisions published by their cutoff. Serve predecessor semantics below the tag. Keep the original observation, selection-time posterior, completion and repair receipts as recorded. The separate discriminating observation and its factor resolution retain G4's closed design.
3. **Storage stop.** `migrations/028_probe_episodes.sql` enforces a unique observation per attempt, and `probe_observations` is a raw ledger. The currently published probe-grade interpretation is a different quantity and the held-at-write branch skips that publication. A second insert in the current table cannot implement supersession. A later landing must demonstrate an existing append-only carrier with the needed identity, inputs and provenance, or secure a migration decision. The design grants no migration allocation.
4. Propose **`mvp-0.71`**. The checkout chain ends at `mvp-0.68`. The Reader and the lesson-weight proposal account for `.69` and `.70`. The G2 design also still names `.69`, so the orchestrator must reconcile the chain at landing. Append only the actual immediate successor, with a tag predicate, whole-vault rebuild activation and matching `EXPECTED_ACTIVATIONS` row. Ensure replay explicitly projects affected episode marginals (`learner_state_beliefs` is classified COMPAT). The projection must be prepared before version publication. Check version/default/identity changes and rebuild equivalence. The November 16 owner rule specifies a tag without a kill switch. [In-flight reservations](algorithm-mvp-0.70.md) · [G2 proposal](refactor-g2-design.md)
5. Start the successor with the strategy's two fail-first tests in `tests/test_probe_held_release.py`, `test_a_released_hold_moves_the_episode_posterior` and `test_a_regrade_of_a_probe_answer_moves_the_episode_posterior`. Use a discriminating card and explicit expected posterior. Exercise real submission, revision and replay. Check a still-held and an exposed answer, a second revision, retry, the old tag and the original receipt. The existing journey goldens characterize the predecessor.

**Owner-copy gate.** On fresh SQLite backup-API copies, record the live source hashes. At the predecessor, count presented attempts held at submission, released, currently held, regraded and exposed. Capture their grade revisions, locked sets, effective outcomes, discounts, posteriors/counts and persisted misconception beliefs. Capture mastery, facets, due dates and schedule effects with `learnloop rebuild --shadow --json`. Upgrade a sibling copy through the immediate predecessor to the successor. Compare those same readings, raw receipts and causal resolutions, run foreign-key checks and doctor, then rebuild twice and verify identical successor projections. Each belief delta must trace to an admissible changed epoch and its subsequent evidence. G3 measured zero released or regraded probe answers on its November arxiv copy. A fresh copy can still have zero cases, so require a discriminating synthetic positive control. Verify the live hashes again. This gate has not run.

Generated references are left for the orchestrator. K9.17 has no implementation, tag, schema, prompt or switch change in this checkout.
