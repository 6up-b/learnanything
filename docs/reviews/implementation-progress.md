**Review fixes implementation**

Authorized scope: merge current PR, implement P1–P2 findings from both September 6 reviews (except withdrawn process-tree termination), proposed test improvements, and original data recommendations 1–5. Background work must survive debug restarts where its owner remains alive. No paid model calls are needed for validation.

Base: PR #4 merged as `472128f527b9b4b02aa6581cc26b4a623870b371`; local checkout fast-forwarded. Working branch: `fix/review-recovery-and-telemetry`.

Implementation checklist:

- [x] Durable submission continuation and result recovery without double grading or premature feedback.
- [x] Atomic live rebuild publication, protected from concurrent evidence writes.
- [x] Ingest ownership fencing, conditional stale recovery, periodic expiry checks.
- [x] Per-call inventory/window/evidence checkpoints and usage; bounded failure-aware concurrency.
- [x] Single provider retry policy, truncation classification, correct HTTP deadline, propagated generation budgets and cumulative checks.
- [x] Cached apply/goal continuation, versioned legacy request identity, durable legacy windows and extraction reuse.
- [x] Reader partial completion, late listener cleanup, manual health/reconnect, independent native resource access/range reads.
- [x] Exact offer provenance, honest final policy probability semantics, eligible versioned outcome labels, immutable decision-time features.
- [x] Test fixture templates, redundant test consolidation, shared AST/simulation results, real lifecycle and transport fault tests, explicit durability lane.
- [x] Versioned event/outcome collection contract and provider-call receipts, including unavailable/pending/censored states.
- [x] Read-only data quality report with current-version denominators and actionable invariants.
- [x] Consistent dataset snapshots/export manifests and stable chronological/grouped splits.
- [x] Production-durability concurrency benchmark; retain current journal mode unless measured evidence supports changing it.
- [x] Focused checks, full Python suite, import contracts, frontend tests/typecheck/build, Rust tests, final diff review.

Implementation is committed as `0395ae3`. See [implementation notes](2026-09-07-implementation.md) for behavior, commands, benchmarks, and limits.

Validation:

- Full Python suite: **4,561 passed**, 10 dependency/SQLite-adapter deprecation warnings, **1,011.76 seconds (16m 51s)**. The review baseline was 4,402 tests in 1,954.22 seconds; the test set and implementation differ, so this is not an isolated attribution of the speedup.
- A final late-receipt ownership case was added while the full run was in progress. Its focused group passed **103 tests**; two socket tests blocked by the sandbox passed outside it (**2 passed**). Thus the new 4,562nd case is separately verified.
- Production SQLite durability lane: **8 passed** (4,554 deselected). Connection ownership/atomic rollback, ingest takeover, late-usage preservation and concurrent backup use production settings.
- Frontend: **13 lifecycle tests passed**, TypeScript check passed, production build passed. Main JS is **1,251.12 kB**, 370.82 kB gzip; large-chunk advisory remains.
- Rust: **20 tests passed**.
- Import architecture: **6 contracts kept, 0 broken**.
- Focused final migration/export/serializer/rebuild/provider boundary group: **88 passed** before the final full run.
- `git diff --check` passed. Ordinary historical fixtures remain unchanged; the dedicated schema-head fixture was upgraded with the migration service and renamed to head 163.
- Read-only `doctor --data-quality` ran against `fixtures/linear_algebra`; its [report](artifacts/linear-algebra-data-quality.json) keeps legacy missingness separate from current-version alerts.

No paid provider calls or production-vault migrations were used for verification. The implementation notes explicitly describe partial provider coverage, unknown viewing/burden, Codex's advisory budget, and the decision to retain production DELETE journaling.

The database/configuration reference was regenerated from code commit `0395ae3`. Its validator passed with **258 table notes, 299 owned notes, 3,365 Wikilinks checked, and zero errors**. A stale reference to the moved `REFACTOR_PROPOSAL.md` was corrected. The generated reference is isolated in the documentation commit for review.
