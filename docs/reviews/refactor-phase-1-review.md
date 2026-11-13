# Phase 1 adversarial review (2026-11-13)

The owner's rule (strategy §2.19): after each phase lands, a Codex `gpt-6-astra` adversarial review of the phase's whole diff, then one fix round. This is the first. **Range:** `ad194ddc3a` (arc C's close review) to `412cc63b4b`, 221 commits: K0-K3, D1, D2a, D2b and its parts, D3, the ledger fixes D-1 to D-27, the facet-belief successor mvp-0.59, M0, K2.1, K2.2, T3 and K1's fixes.

**How.** Five reviewers, read-only, effort high, one area each, briefed to attack the steps' records. Their reports are kept whole in `docs/reviews/artifacts/phase-1-review/codex-<area>.md`. They ran no code. The orchestrator read the code behind 9 of the 38 findings (marked "read" below) and all 9 hold. The rest are confirmed or dropped by the fix round: each fix starts from a test that fails at the tip, and a finding whose test can't be made to fail is closed as not reproduced, with the evidence.

**Result.** 38 findings: 19 high, 18 medium, 1 duplicate (P8 is T7). About half were introduced or left half-fixed by the phase's steps, and half are older defects the steps touched without protecting. Two change advice already given to the owner: U1 and S1 mean the mvp-0.59 upgrade waits for the fix round.

## Findings

Ids: U upgrades and floor, S the mvp-0.59 successor, I ingestion, P protection, T tests. "New": introduced or left half-fixed in this range. "Old": predates it.

### Upgrades and the floor (`codex-floor.md`)

| Id | Sev | Finding | New or old | Checked | Fix |
|---|---|---|---|---|---|
| U1 | high | The tag rewrite replaces the first matching text, so a comment holding `algorithm_version = "<predecessor>"` is changed instead of the setting; the upgrade commits the successor's state and reports success while the config still names the predecessor. Nothing reads the tag back. | old (kept by D3) | read | FR-A |
| U2 | high | A sidecar already bound keeps serving its cached vault after a reload is refused below the floor, and after another process leaves an activation journal. | new (D1), journal part old | | FR-A |
| U3 | high | A journal that can't be read (a permission or I/O error) is treated as torn and deleted, though the config may already name the successor. | old (kept by D3) | read | FR-A |
| U4 | medium | The MCP runtime advances its freshness time before loading, so the request after a below-floor refusal serves the old snapshot. | new (D1) | read | FR-A |
| U5 | medium | `learnloop doctor --fix` rewrites provider settings in a below-floor vault's config before `run_doctor` refuses it. | new (D1) | read | FR-A |
| U6 | medium | `learnloop mcp activity` and project enrollment load the config directly and never meet the floor. | new (D1) | | FR-A |
| U7 | medium | The `pre-floor` restore route can't run `recurrence guard`, which an old upgrade can require: at that tag only `upgrade` may open a vault below the floor. | new (D3) | | FR-A |
| U8 | medium | The replacement upgrade tests no longer assert that the mvp-0.58 to mvp-0.59 activation derives the successor's state (uncertainty rows, the corrected streak): a receipt-only activation would pass. | new (D3) | | FR-A |

### The mvp-0.59 successor (`codex-successor.md`)

| Id | Sev | Finding | New or old | Checked | Fix |
|---|---|---|---|---|---|
| S1 | high | The uncertainty rows are derived with today's criterion-to-facet mapping, not the frozen contract: after an item's mapping changes, a rebuild moves an old failure to another facet while the belief stays. Live and replay disagree. Explicit `criterion.targets` are also ignored when `criterion_facet_weights` is absent. | new (D-5) | | FR-D |
| S2 | high | With the kill switch off, `valuation.facet_problem`, the Reader's `open_questions` and tutor promotions still read stored uncertainty rows directly. | new (D-5) | read | FR-D |
| S3 | medium | A row rekeyed after a facet alias change keeps hypothesis labels naming the old facet, so a solid facet reads as a known gap. | new (D-5) | | FR-D |
| S4 | medium | With `repeat_surface_discount = 0` a full-marks answer has zero positive mass and skips D-1's reset. | new (D-1 incomplete) | | FR-D |
| S5 | medium | Doctor's stale-switch warning compares only the current switch with the last rebuild's, so off-then-on with attempts between leaves a stale posterior and no warning. | new | | FR-D |
| S6 | medium | The evidence timeline counts an older unverified failure that the projection leaves out, so Demonstrated undercounts later credit. | old | | FR-D |

### Ingestion (`codex-ingestion.md`)

| Id | Sev | Finding | New or old | Checked | Fix |
|---|---|---|---|---|---|
| I1 | high | The apply's pre-image is taken after staging, by diffing the staged tree against the live one: a file edited while staging ran is recorded as the pre-image and overwritten. | old (K3.5 left it) | | FR-B1 |
| I2 | high | Deleting a pending proposal item is not refused while an apply intent is outstanding; recovery then applies the deleted item's content with no inbox row to undo it. | new (D-10 incomplete) | read | FR-B1 |
| I3 | high | The collection build treats "has an inventory row" as "already synthesized", so a unit inventoried earlier and never synthesized is left out of the append. Its own test asserts the loss. | new (K3.3) | read | FR-B1 |
| I4 | high | A completed shard is keyed on its first pass only: a changed second (span) request is answered from the shard. | old (K2.2 kept it) | | FR-B2 |
| I5 | high | D-9's discard is by request key, not by the answer judged: a slower run can delete a newer paid answer saved under the same key. | new (D-9) | | FR-B2 |
| I6 | medium | A reused shard's span-round answer survives a gate rejection and is replayed into the retry. | new (D-9 incomplete; its record said so) | | FR-B2 |
| I7 | medium | The book card's undo checks for an outstanding intent before taking the lock, then moves the generation and cancels builds before the guarded reject refuses. | new (D-10 incomplete) | | FR-B1 |
| I8 | medium | A re-inventory after a prompt edit returns a new inventory id that the upsert did not store. | new (K2.2 exposed it) | | FR-B1 |

### Protection (`codex-protection.md`)

| Id | Sev | Finding | New or old | Checked | Fix |
|---|---|---|---|---|---|
| P1 | high | The gate checks the file on disk, not the loaded snapshot it then reads: a vault loaded while the file was empty passes once the file is restored. | new (K1-1 incomplete) | | FR-C |
| P2 | high | `_reader_source_sets` returns an empty list when `learnloop.toml` is missing, which skips the gate. | new (K1-1 incomplete) | read | FR-C |
| P3 | high | Two source-set saves that read the same file overwrite each other; an exam membership can vanish. The CLI takes no vault lock. | old | | FR-C |
| P4 | high | MCP `find_sources` with verify sends reserved, probe, solution and assessment-lane passages to the verification model and filters them only afterwards. | new (K1-4 incomplete) | | FR-C |
| P5 | high | K1-6's reservation is in the out-of-timing set only: the routine due queue never reads it, so ordinary practice can still serve the cold item. | new (K1-6 incomplete) | read | FR-C |
| P6 | high | An expired or withdrawn cold retry leaves its episode's item reserved for good. | new (K1-6 made it bite) | | FR-C |
| P7 | medium | The atomic write replaces a symlinked `source_sets.yaml` instead of writing through it. | new (K1-1) | | FR-C |
| P8 | medium | Same as T7. | | | FR-E |

### Tests (`codex-tests.md`)

| Id | Sev | Finding | New or old | Checked | Fix |
|---|---|---|---|---|---|
| T1 | high | The recovery tests that fed a wrong-scope receipt (a startup projection, a per-LO rebuild at the target tag) and required the activation to run anyway were deleted with the chain. | new (D3) | | FR-A |
| T2 | high | The phone's stop-and-handoff journeys now run only on the staged frame; the objective's boundary prefetch with a pending stop has no test. | new (D2b part 2a) | | FR-E |
| T3 | high | The default pin replaces `keep_going`, and the one refinement test supplies its own: production's refinement controller has no test. | new (T3) | | FR-E |
| T4 | medium | `test_stuck_prompt_replay` became a head-to-head idempotence check; replay of older `dont_know` rows is no longer tested. | new (the mechanical re-tag) | | FR-E |
| T5 | medium | The mixed-model recurrence guard test lost its rejection assertions with the upgrade call. | new (D3) | | FR-A |
| T6 | medium | Two distribution tests (`test_ro5_checks`, the TE1b spread) now measure the pinned seeds, not production's seed derivation. | new (T3) | | FR-E |
| T7 | medium | Identity pin C3 hashes a dictionary the test builds, not the boundary the chooser assembles. | new (K0) | | FR-E |
| T8 | medium | The ratchet's import visitor drops any branch whose condition mentions `TYPE_CHECKING`, including `if not TYPE_CHECKING:`. | new (M0) | | FR-E |

## The fix round

One fix round, in groups by file so they don't collide. Each fix: a test that fails at the tip, the smallest change, the ledger row. Behaviour that the learner sees changes only where a row says so.

| Group | Rows | Who | Notes |
|---|---|---|---|
| FR-A | U1-U8, T1, T5 | Opus | Structure and failure handling in `ops/upgrades.py`, the doors and the upgrade tests. U1 first: the owner's upgrade waits for it. |
| FR-C | P1-P7 | Sonnet, then the orchestrator's read | Each has a precise failing test in the report. P5 and P6 change what the queue serves, as K1-6 meant to. |
| FR-D | S1-S6 | Opus, under the playbook | Behaviour track; lands alone. If no vault holds mvp-0.59 the successor is amended under its tag before anyone upgrades; if one does, the fixes are a new successor. The owner says which. |
| FR-B1 | I1, I2, I3, I7, I8 | Sonnet | The apply protocol, the collection build, the inventory upsert. |
| FR-B2 | I4, I5, I6 | K2.3's implementer, after K2.3 | Same files as K2.3 (`source_set_synthesis.py`, `source_append.py`). |
| FR-E | T2, T3, T4, T6, T7, T8 | Sonnet | Tests and the ratchet's parser only. |

After the round: this record gains each row's outcome (fixed with its commit, or not reproduced with the evidence), and the next phase starts.

## Outcome of the fix round (closed 2026-11-13)

All 38 rows are closed: 36 fixed from a test that failed first (or, for the test rows, from a production mutation that the existing tests missed), 1 restored though it did not reproduce as a gap (T5), 1 duplicate (P8). Each group's record has the failing test, the fix, and the callers and siblings checked: `docs/reviews/refactor-phase-1-fixes-{upgrades,protection,successor,ingest-apply,ingestion-synthesis,tests}.md`.

| Row | Outcome | Commit |
|---|---|---|
| U1 | fixed: the setting is written through the TOML writer and the tag is read back before the commit | `5ec258a0b9` |
| U2 | fixed: a bound sidecar refuses every request and worker until a load succeeds | `07620e5839` |
| U3 | fixed: one journal reader; a read error refuses and keeps the file | `94ad5dad87` |
| U4 | fixed | `abb8739ee1` |
| U5, U6 | fixed: every CLI root resolver meets the floor first (five new doors tested byte-identical) | `a477e94204` |
| U7 | fixed as a true statement: a vault below mvp-0.12 with `recurrence.require_guard = true` needs that key set false at `pre-floor`; the refusal and ADR-019 say so | `0fc27938a0` |
| U8 | fixed: the activation's derived state is asserted (kills a receipt-only mutant) | `11f9793801` |
| S1 | fixed: the uncertainty outcomes come from the attempt's contract rubric | `d7a9ee75d3` |
| S2 | fixed: one reader honours the switch; a test pins that only it reads the table | `6500874367` |
| S3 | fixed: labels follow a rekey; the chain continues under an earlier id | `755835d316` |
| S4 | fixed | `86da3bce2a` |
| S5 | fixed: each attempt records how it was derived; doctor warns on any mismatch | `4b14ab7e6f`, `abaa90304e` |
| S6 | fixed: the timeline leaves out what the projection leaves out | `9b4de2ef50` |
| I1 | fixed: staging is hashed as it is copied; only files the items change are targets | `ac0f886a09` |
| I2 | fixed: delete refused; edit and refresh refused for an item an intent names; recovery fails loudly | `af63b23d8c` |
| I3 | fixed: the collection build asks `units_not_yet_sent` | `cb31485d14` |
| I4 | fixed: a shard that recorded a span round reruns its passes from their checkpoints | `d711ca58c4` |
| I5 | fixed: a discard names the stored answer it judged (five sibling discards too) | `4c1d4bad96` |
| I6 | fixed | `844d349340` |
| I7 | fixed: undo's check and changes under one lock | `7bce316feb` |
| I8 | fixed | `249ae4e93c` |
| P1 | fixed: the snapshot carries the load's verdict | `1349efbe92` |
| P2 | fixed | `962f8f0030` |
| P3 | fixed: the read-modify-write runs under the vault lock | `32bf64016a` |
| P4 | fixed, and its sibling: the tutor's `find_sources` and `compare_sources` tools | `6aa0c53be2`, `1b931368a1` |
| P5 | fixed, then narrowed: the routine queue withholds only while a cold retry is open (two named readers) | `9d4f2dd25a`, `acd879b283` |
| P6 | fixed: an expired or withdrawn retry releases; the refusal branch releases | `ab1431ee12`, `babee7d002` |
| P7 | fixed | `b8b584c916` |
| P8 | duplicate of T7 | |
| T1 | fixed: wrong-scope receipts no longer pass (kills a mutant) | `452b01ff44` |
| T2 | fixed: the three stop-and-handoff journeys also run on the objective path | `eaa0cd5e6a` |
| T3 | fixed: the real refinement job is tested with a gated model and a moved clock | `e284c4d77a` |
| T4 | fixed, and one more loss found by the audit (`test_followup_reserved_only`) | `5e31592dfb` |
| T5 | restored; not reproduced as a gap (three borrowing mutants were already caught) | `44e0c69222` |
| T6 | fixed: three distribution tests marked `real_draws` | `abcb878933` |
| T7 | fixed: a new pin `C3b.chooser` drives the chooser's own assembly | `557eb3c95b` |
| T8 | fixed: the visitor reads the guard structurally | `216c1f2910` |

**Left open by the round** (each is a ledger row): the bound runners after a sidecar refusal; the lifetime of an unstarted remediation episode (the owner's); the inventory row's I4 shape; the rest of S1 (three inputs still read today's item); a massless walkthrough and the failure streak; Demonstrated above banked credit on one copy; block order under the objective with every seed fixed (D-28, not seen in T2's journeys with the numeric seed fixed).

## What the review says about the process

- **A fix named by one site was fixed at that site.** K1-6, D-9, D-10 and K1-1 each repaired the path their ledger row named and left a sibling path open (the routine queue, a concurrent run, deleting a pending item, the snapshot). Fix briefs from here ask for every caller and every sibling of the function changed, listed in the record.
- **Tests written with a fix asserted the fix's own reading.** I3's test pins the coverage loss as intended behaviour. A step's proof and its tests share the step's blind spot; the outside review is what catches it.
- **Old defects surface when code moves.** U1, U3, I1, I4 and P3 predate the refactor. Moving the code under review is how they were seen.
- **Pins and frames buy determinism and cost coverage.** T2, T3 and T6 are the price of T3's default and of the staged frame; each needs one test on the real path, marked `real_draws`.
