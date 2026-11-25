# L4-2's fit: recorded facts instead of inference (design note, 2026-11-25)

**Recommendation: option (a), recorded facts, in the form below: no migration, tag `mvp-0.75`, a whole-vault
rebuild.** Mastery records what it did on each application in the per-attempt record it already rewrites on every
application, live and replay. The lesson-weight fit reads those facts through one reader, and every reader of a
lesson outcome uses one tag-aware order. The frozen curve `(a, b)` remains the only grade-time fact, as the owner
decided (option 2, 2026-11-23).

## Why a third patch round is the wrong move

The second adversarial review (2026-11-25) of the first fix round
([algorithm-mvp-0.72.md](algorithm-mvp-0.72.md#review-fix-round-the-adversarial-review-of-2026-11-24)) found most
first-round fixes only partly done, plus a dozen new defects. Nearly all of them have one cause. The fit
works out, from stored numbers, what mastery did:

| What the fit infers today | How | Where the inference breaks |
|---|---|---|
| whether an update applied | `mu_before != mu_after or P_before != P_after` | a floor-bound update at the mean cap leaves both numbers equal (re-review "R7") |
| the grader-interpretation noise | inverts the variance step | wrong whenever the floor set the variance, so first-round R7 labelled those updates and sent them to the first-order form |
| the observation instant | the attempt's `created_at` (whole seconds) | live mastery used the subsecond clock (re-review "fractional second") |
| the drift clock | advances on "applied and not primed" | inherits the `applied` edge |
| that the endpoint matches mastery | compares when the outcome's prior exists, passes silently when it does not | fails open (re-review "R8") |
| the check's score in the first-order form | the immutable `sensitivity.correctness` | a regraded check scores its old grade (re-review "first-order") |
| outcome order | the fit takes `attempt_order_for`, the other two readers take the default `LEGACY_ORDER` | one answer is learned and reported as opposite outcomes (re-review "R6") |

Each patch closes one edge, and the next mastery step (another clamp, another floor, another clock rule) opens a new
one. The owner's standing rule calls for a larger change here.

## The options

**(a) Recorded facts.** Each time mastery applies a grade it records, in the payload it already writes for that
attempt (`attempt_debug_payloads`, rewritten by every LO replay and rebuild together with `attempt_surprise`), a
`mastery_application` block. The block holds:
- whether the update applied;
- the prior `(μ, P, last_evidence_at)`;
- the observation instant as a string at the precision used;
- the score mastery read;
- the `(a, b)` it applied;
- the observation weight and the interpretation variance it was given (not recovered);
- `primed`;
- the coverage floor;
- the posterior after the floor.

The fit reads the blocks through one reader (`mastery_applications`) and recomputes only the varied check mass. The
blocks have to chain: each prior must equal the previous posterior, to the bit, including the evidence clock. A
break means another writer moved the state, such as a re-anchoring claim. It is a fact comparison, not a tolerance.
The outcome's own block is required. If it is missing, the trace says so and the fit takes the first-order form; it
no longer fails open. When the frozen pair and the pair mastery applied differ, the trace records both. The first-order
form reads the check's block and the current score of the check's current epoch. A reproduction guard at the
recorded mass remains, but its only job now is to catch a configuration changed since the facts were recorded.
`qualifying_outcomes` takes its order as a required argument, and `outcome_order(version)` is the single place it
comes from.

*Why not a raw table beside the curve, as the brief suggested.* The trajectory needs mastery's **current**
application. After a regrade of an earlier answer, replay moves every later prior, and a grade-time row would then
describe a trajectory that mastery no longer holds. The facts have mastery's lifecycle, so they belong in the record
mastery rewrites. The curve is different: the owner froze it on purpose so that content edits cannot move old
windows, and it stays in the raw `attempt_grade_curves`.

**(b) Keep inference and patch each edge.** The patches would be: read `applied` from the payload's floor being
non-null, require the endpoint prior, compare the pairs through the surprise row, truncate the clock, and pass the
order to the two readers. Each is small. The noise inversion and the clock inference stay, and the class stays with
them.

**(c) First-order only.** Drop the trajectory likelihood. That removes the floor, noise, clock and endpoint edges.
It does not touch outcome order or the stale score in the first-order form itself, and it reverses the TE1 review's
F6, which the owner accepted. Every fitted window would change meaning. **This option needs an owner decision.**

## Judged

The table counts the re-review findings assigned to this round, as removed **by construction**. Fixes needed under
every option are listed under it.

| Finding | (a) facts | (b) patch | (c) first-order |
|---|---|---|---|
| floor-bound update with equal numbers | yes: `applied` is recorded | patched | yes |
| endpoint fails open; endpoint-only pair disagreement | yes: the block is required and the pair is compared | patched | yes |
| a regraded check scores its old grade in the first-order form | yes: reads the current epoch and its block | patched | **no**: the same bug remains |
| ordering differs between the fit, the report and the router | yes: one required order | patched | no |
| fractional-second instant | the fit reads the recorded instant | patched | yes, on the fit's side |
| first-round R7's lost noise (floor-bound updates sent to first-order) | yes: the noise is given, not recovered | no | yes |
| **Under every option** | | | |
| mastery itself: live versus rebuild | mastery observes at whole seconds from the tag (one line) | | |
| check stamped before the writer lock | service fix | | |
| R4 same-bucket freeze | freeze rule | | |
| R12 compaction | compaction fix | | |
| minors | record fixes | | |

**Cost of (a).**
- Schema: no migration. Migration 276 is not taken.
- Upgrade: one tag, `mvp-0.75`, with a `whole_vault_rebuild` row. The rebuild rewrites every payload with its block, so all history gets the facts. No "unknown at upgrade" marker is needed for mastery facts. The curve's `missing_at_upgrade` and `missing_capture` markers stay as they are.
- Code: about 30 lines in `attempts.py`, a file other workers also touch (the payload block and the whole-second instant at the tag). The trajectory reader in `lesson_weight.py` is rewritten under the tag. Below the tag it is unchanged.
- Goldens: payload goldens at the latest tag gain the block. Identity pins that hash the tag move.

**Owner data.** None of the three owner copies holds a lesson check or a trace row, so there is no fitted history
to preserve. On those copies the rebuild changes only payload JSON. Mastery's replay already observes at whole
seconds.

(a) removes the inference rather than another instance of it, needs no owner call, and costs least in schema terms,
so it is the recommendation. R9 stays an owner call either way: calibration identity per epoch, versus retroactive
reinterpretation with a rebuild on import. Under (a), the block records the interpretation variance as applied. That
makes R9's first option a matter of reading the block's value on replay rather than recomputing it.
