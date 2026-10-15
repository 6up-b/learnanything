# Algorithm-change playbook

Use this process when scoring, scheduling, projection, or admissibility
semantics change. A code change is not complete merely because new attempts use
it; existing vault history must remain interpretable and reproducible.

1. Decide whether the change alters persisted meaning. If it does, add a new
   immediate-successor `algorithm_version` in
   `learnloop.algorithm_versions`. Never silently reuse an old tag.
2. Keep raw ledgers and append-only receipts immutable. Add a correction or
   reinterpretation event when history needs new meaning; do not update the
   original evidence.
3. Add or update the explicit vault-upgrade function. It must refuse jumps,
   prepare the candidate projection before the atomic config rename, and leave
   the prior version readable if preparation fails.
4. Update the effective-default fingerprint keyed by the new version. A default
   change without a version/fingerprint decision is a reproducibility bug.
5. Classify every new table in `learnloop.db.table_roles`. A new `DERIVED` table
   must have exactly one registered rebuild owner; a new `RAW_LEDGER` or
   `RECEIPT` table must never be cleared by replay.
6. Extend replay-completeness and rebuild-equivalence tests. The same-version
   rebuild on the golden fixture must reproduce the same semantic projection,
   ignoring only explicitly documented surrogate IDs and write timestamps.
7. Run a shadow rebuild against a copied database and inspect mastery, facet,
   and scheduling deltas before applying the version to a live vault. Verify the
   live database hash is unchanged.
8. Add or regenerate a fixture at the migration head and exercise the complete
   predecessor-to-successor upgrade path, foreign-key checks, doctor, and a
   second idempotent rebuild.

New vaults start at `LATEST_ALGORITHM_VERSION` (owner decision 2026-10-12,
Slice 1 M2 open question 1). The successors form one linear chain,
`SUCCESSOR_CHAIN` in `learnloop.algorithm_versions`: a successor merge appends
its tag there (`LATEST_ALGORITHM_VERSION` and every version gate, such as
`DIAGNOSIS_SPLIT_VERSIONS` and `PLACEMENT_VERSIONS`, follow) and adds its
defaults snapshot.

Recorded exception, not a rule: on 2026-10-12 the owner's placement decisions
amended `mvp-0.11` in place, hours after it merged and before any vault this
repository tracks had reached it (as the PF-c fix amended `mvp-0.10`). The
amendment is recorded beside the version and in
`docs/reviews/placement-owner-decisions.md`, with items 4 and 6-8 run for it.
Any other in-place amendment takes its own owner decision; by default a change
to persisted meaning mints a new tag.

Recorded owner decision, 2026-10-13 (route-check-in-grader): mvp-0.17's
separate proofs route check was removed from serving. Its kill switch already
defined that state (`proof_check.enabled = false` grades new answers as
mvp-0.16), so an mvp-0.17 vault now serves that permitted state without a new
tag, while its records keep their meaning and replay exactly
(`fixtures/mvp017_route_check_replay`). The rules that replaced it change
grading for new answers, so they mint a successor (built as mvp-0.18, a
placeholder, and relabelled mvp-0.20 at its merge after the sources track;
mvp-0.18 and mvp-0.19 vaults also grade new answers without the check).
See `docs/reviews/route-check-in-grader.md`.

Recorded owner rule, 2026-10-13 (method-explicit items): rubric criteria name
the fact a step establishes, not the method; an item whose target IS a method
records it as `PracticeItem.required_method` and is presented with the
instruction "Use {method} in your answer." rendered from that field. The
grading side changes grading for new answers on required-method items (a
criterion tied to the required method is graded on use of that method,
`own-route-v2`), so it mints a successor, built as `mvp-0.22-placeholder` and
relabelled mvp-0.25 at its merge after router R2b + R2c (mvp-0.24), with the
kill switch `required_method.enabled` grading exactly as mvp-0.24. The
generation side
(criteria phrased by fact on every writer, the required method written only on
a method target) is a content change, and existing method-phrased criteria are
flagged (`criterion:method_phrased`) and repaired only through proposals the
owner confirms, never rewritten. An answer is graded under the required
method its assessment contract froze when the item was presented, never one
the item gained later (grading and regrading alike); while the rules are on, a
regrade of a required-method item also reads the statement and rubric from
that contract, and its rows cite it, so a content edit never changes how a
past answer's method is enforced. The field is the ONE authority (redesign,
2026-10-14): grading, regrading and replay never parse the prompt to decide
whether a method applies. The instruction is never stored in the statement
(round 3): it is rendered from the field as a separate block wherever the
item is shown, and into the grader's question from the frozen contract, so
no writer appends it, no validation looks for it and nothing edits a
statement to add or remove it. A textbook statement is judged once at import
by the Decider, else the LLM judge, ledgered; a PF variant's stem is judged
once before publication; a statement reader survives only as an advisory
doctor/report flag. A frozen regrade binds the key status of the content it
graded, not the item's current content, and a historical one whose inherited
default rubric cannot be recovered binds unverified. See
`docs/reviews/method-explicit-items.md` and
`docs/reviews/method-explicit-items-codex-review.md` ("Redesign").

Changes in `learnloop.substrate.compat` require a separate compatibility
decision and a fixture representing the historical vault shape. They are never
folded into an algorithm bump as incidental cleanup.
