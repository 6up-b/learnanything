FINDINGS

1. HIGH — Diagnostic replay uses today’s facet mapping, moving historical failures between facets

Where: src/learnloop/attempts/attempts.py:2834, :2878, :4560, :4929; src/learnloop/learner/recall_coverage.py:255, :763. Newly persisted on canonical vaults by 0dda03e99a.

Scenario: An item has criteria c1→alpha and c2→beta. The learner fails c1 and passes c2, opening uncertainty on alpha. Later, the item’s criterion_facet_weights mapping changes to c1→beta and c2→alpha. Replay restores the frozen rubric but passes today’s item to derive_facet_outcomes. Rebuilding deletes the alpha uncertainty and writes beta uncertainty from the old answer. The canonical belief still follows the frozen contract and attributes the failure to alpha.

The same mapping path ignores explicit criterion.targets when criterion_facet_weights is absent, falling back to lexical inference or whole-answer correctness. Thus even an unchanged item can produce diagnostic outcomes inconsistent with its explicit targets.

Why missed: The successor’s replay comparison uses unchanged content. The ported uncertainty replay test likewise rebuilds one unchanged item. Persisting the legacy diagnostic calculation exposed assumptions those tests never challenged.

Smallest failing test: Record the two-criterion attempt, swap only the item’s criterion_facet_weights, then rebuild. Assert that the uncertainty remains on alpha, with the same posterior and opening attempt.

Confidence: Certain from the data flow. Not executed; the exact resulting posterior was not calculated.

2. HIGH — Turning the kill switch off does not disable all uncertainty readers

Where: src/learnloop/instructional/valuation.py:196, :546; src/learnloop/instructional/reader_followups.py:294; src/learnloop/tutor/promotions.py:935. Exposed by 0dda03e99a.

Scenario: An upgraded vault accumulates facet_uncertainty rows with fixes enabled. Set canonical_belief_fixes=false without rebuilding. The canonical reader returns [], but facet_problem still constructs a valuation problem from the stored posterior, and Reader open_questions still adds a facet-based discriminating question. Tutor promotion features also retain the uncertainty snapshot.

The documented contract explicitly promises empty uncertainty reads with the switch off. These are active reads of the disabled feature, beyond the acknowledged persistence of previously derived state.

Why missed: test_with_the_switch_off_the_belief_is_the_predecessors_exactly starts with the switch off and an empty table. It checks the canonical reader, not the direct readers. The doctor test checks only the warning.

Smallest failing test: Create an uncertainty row through an enabled attempt, disable the switch, and call facet_problem. Assert that it returns no problem. A sibling assertion can check that open_questions adds no facet_marginal question.

Confidence: Certain. The returned valuation/question changes are directly supported; I did not execute downstream selection.

3. MEDIUM — Rekeyed uncertainty retains hypothesis labels naming the retired facet

Where: src/learnloop/learner/facet_state_reader.py:97, :371; src/learnloop/learner/facet_diagnostics.py:583; src/learnloop/diagnosis/probes.py:783. Introduced by 0dda03e99a and a733b7d021.

Scenario: A stored, resolved uncertainty row for alpha has facet_solid:alpha as its leading hypothesis. The registry subsequently makes alpha an alias of beta, and the vault is reopened without replaying that LO. The reader changes state.facet_id to beta but leaves hypothesis_marginal unchanged. facet_state_label now calls the previously solid facet a known_gap because facet_solid:alpha does not equal facet_solid:beta.

The likelihood model also treats the stale solid label as unfamiliar when evaluating beta. canonical_uncertainty_rows has the same omission when rekeying newly computed rows.

Why missed: The merge test asserts the destination facet ID and row ID only. It never inspects hypothesis labels or evaluates a consumer after rekeying.

Smallest failing test: Store a resolved alpha row, introduce alpha→beta in the loaded alias map, read it through facet_uncertainty_states_for_lo, and assert that facet_state_label still reports solid.

Confidence: Certain for an unreplayed alias change. The normal merge service replays affected LOs, so this finding concerns registry edits or other paths leaving existing rows unreplayed; I did not exercise those paths through the UI.

4. MEDIUM — A zero repeat discount preserves D-1’s failure streak after full success

Where: src/learnloop/substrate/canonical_projection.py:982, :986, :1016; src/learnloop/diagnosis/followups.py:2433. Incomplete fix in 0dda03e99a.

Scenario: Configure evidence.correlation.repeat_surface_discount=0. Give two failed attempts followed by a full-marks attempt on the same surface. Failures still increment consecutive_failures, including when their discounted mass is zero. The full success has positive=0 and skips the new reset at line 1016. Its negative_fraction is also zero, so the other reset is skipped.

The follow-up gate consequently still sees repeated facet failure after the success. A partial success can reset the streak through the failure loop, making full marks behave worse.

Why missed: The D-1 tests use the default repeat discount, 0.25, so the new success-loop reset is always reachable.

Smallest failing test: Run the existing two-failures-then-success scenario with repeat_surface_discount=0; assert current_same_facet_failure_streak returns zero.

Confidence: Certain. No execution; the configuration reader accepts the zero value directly.

5. MEDIUM — Doctor loses the stale-state warning after a switch round trip

Where: src/learnloop/ops/doctor.py:1643; src/learnloop/attempts/attempts.py:3324, :4354. Introduced for facet uncertainty by 0dda03e99a.

Scenario: Upgrade/rebuild with fixes enabled and establish an uncertainty posterior. Disable the switch, record successful answers, then enable it again without rebuilding. Those answers never updated facet_uncertainty. The next enabled attempt resumes from the old posterior, whereas replay under the current configuration incorporates the intervening successes.

Doctor compares only the current switch with the last whole-vault rebuild’s switch. Both are now true, so it reports no projection_switches_stale warning despite the stale posterior.

Why missed: The doctor test exercises true→false only. It neither records attempts under the alternate setting nor returns to the recorded setting.

Smallest failing test: Extend that test with an attempt while disabled, re-enable the switch, and assert that doctor still warns until a whole-vault rebuild.

Confidence: Certain. The warning predicate and skipped write establish the defect; I did not measure the posterior difference.

6. MEDIUM — Historical unverified failures make the timeline undercount later demonstrated credit

Where: src/learnloop/learner/facet_evidence_timeline.py:656, :764; src/learnloop/substrate/canonical_projection.py:945, :1021; src/learnloop/outcome_contract.py:55. Predates the base; retained by the successor’s claimed projection/timeline equivalence.

Scenario: History contains a zero-point, single-target PF-c row carrying negative_evidence_blocked=valid_alternative_unverified but no unverified_interpretation=unassessed—the explicitly supported older representation. A later verified success measures the same cell and surface.

The canonical projection excludes the old shortfall from failure mass and surface-group marking. The timeline excludes only the newer unassessed representation, then synthesizes a single-target attribution and marks the old surface. Consequently, the later success receives full novelty credit in the projection but only the repeat discount in the timeline—0.25 by default. Transfer scaling applies to both calculations without repairing this disagreement.

Why missed: The successor’s timeline equality test contains one fully successful attempt. It has no preceding legacy unverified failure.

Smallest failing test: Add that historical zero-point row before a verified success on the same surface; assert the final Demonstrated value equals banked certification credit.

Confidence: Certain from the two folds and the compatibility predicate. Not executed against a historical vault.

CHECKED AND FOUND SOUND

The three canonical booking changes share the tag-and-switch predicate; the timeline’s transfer multiplier uses that same predicate.
D-3 scales pseudo-mass before both positive and negative allocation and reads the frozen criterion tier.
D-6 books attributed total-failure mass, skips unresolved/unverified failures, and prevents a later same-group success from adding independent mass again.
Ordinary positive-mass full successes reach D-1’s reset, which the follow-up streak reader consumes.
facet_uncertainty has one registered DERIVED owner and is included in shadow comparisons.
The mvp-0.59 upgrade uses whole-vault rebuilding inside the activation transaction, with journaled configuration publication.
D-27 leaves direct uncertainty reads denied in every AD scope; I found no concrete indirect leak in the inspected paths.
The D-27 carve-out removes only that table’s comparison; downstream writes remain compared, and the contract test is no longer xfailed.
Backdated exam seeding explicitly replays affected LOs chronologically.

COULD NOT CHECK

No tests, programs, network requests, or mutations were performed. All proposed failing tests remain unexecuted.
Actual posterior values, selected follow-ups, shadow deltas, crash recovery, and live-versus-replay equivalence require execution.
The deleted backup copies described in refactor-dfb.md were unavailable for inspection.
A complete dynamic audit of every AD-readable table and externally supplied input would be needed to establish indirect noninterference beyond the paths inspected.