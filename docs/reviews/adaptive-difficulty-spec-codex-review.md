# Stage "adaptive-difficulty-spec": Codex review and fixes

**Branch:** `docs/adaptive-difficulty-spec` (base `4108e1ccd`).
**Reviewed:** `4108e1ccd..docs/adaptive-difficulty-spec` at `6a6093457` (the spec `docs/specs/spec_adaptive_difficulty_v1.md` and its research appendix). Codex job `20261014-205612-uLNDmj`.
**Fixed in:** `99a2d811c` (2026-10-15).

This is a documentation stage: no code, migration, config or test changed, and no paid call was made. No finding concerned an external source, so the fix step needed no web search and added no source.

## Review

A spec cannot fail a test, so each finding was reproduced by checking its claim against the code in this worktree and against the other specs. All eight reproduced, so none was rejected. Each fix names the fail-first tests the implementing phase must write (spec §14).

| ID | Severity | Title | Verdict | Commit | Reproduction and fix |
|---|---|---|---|---|---|
| F1 | High | Level numbers have no stable goal or ladder identity | fixed | `99a2d811c` | **Reproduced:** §9.3 keyed credit by `(facet, capability, rung)` and §9.4 stored a bare required level, while §9.1 derived each cell's rungs from whichever exam or milestone target applied. Certification is derived on read, with no durable certificate table (`goals/certification_cold_probe.py:46-55`), so a new target would silently re-mean every stored rung and every re-derived certificate. **Fix:** §9.1: immutable ladder instances, identified by capability, target, schema and version, read per goal. §9.3: `facet_capability_feature_credit` stores each observation's conservative tuple, never a level. §9.4: requirements are feature points; `p_req` reads no goal; the certificate's content hash includes each component's `p_req`, so a changed requirement is a new certificate. Tests G-AD4-9 (two goals sharing a cell), G-AD4-10 (target revisions), G-AD4-11 |
| F2 | High | Item selection can invalidate the router's admitted block | fixed | `99a2d811c` | **Reproduced:** §6.1 drew from the whole cell pool, with no block, minutes or constraint condition. Blocks are packed to at most 15 minutes (`daily_plan/types.py:52`); the staged frame refuses items before packing (`daily_plan/staged_frame.py:9-16`); R2b's mixture draws only reversible candidates (`:42-52`). **Fix:** §6.1: AD draws only at a `new_admitted` slot of the block already chosen (`daily_plan/engine.py:1555-1557`). The support is the slot item plus items that pass the constraint engine on a fresh snapshot, are reversible, are planned nowhere else, fit the block's, plan's and lane's minutes, and add no unadmitted load (`daily_plan/admission.py:142-201`). Checks, draw, substitution and `item_served` are one transaction, so nothing is recomputed or refused after the draw. §10.1: the logged propensity is that of the pair, `π_router · π_AD(i | block, slot, S)`. Tests G-AD3-9 (an item over the block budget), G-AD3-10, G-AD3-11 |
| F3 | High | AD5 does not define executable probe conditionals | fixed | `99a2d811c` | **Reproduced:** §6.3 said AD "supplies `P(Y | H, x)`" over its three categories, while instruments use family alphabets (`classify_outcome`, `diagnosis/probe_families.py:720-786`). The probe spec requires selection and update to use the same grader-composed conditionals, with the resolved snapshot persisted (`spec_probe_eig_redesign.md` §7.2, §9.3; `probe_families.py:267-290`; `diagnosis/probe_episodes.py:1828-1846`). Nothing said how the two meet. **Fix:** §6.3 `ad_probe_compose_v1`. AD supplies one number per capability slot, `q_h`, and replaces only the split between the success class and the rest of the card's calibrated row, before the grader channel. The success class equals `Y = 2` because a diagnostic block disables help and reveal (`probe_episodes.py:70-77`) and, for rubrics of at most 4 points, correctness ≥ 0.8 means full points (`attempts/attempts.py:3295`). The constraint table for capability slots is explicit; misconception slots are untouched; calibration ownership is stated; the composed rows are frozen in the snapshot that scoring and update both read. The amendment to the probe spec's two MUST clauses is stated, under the AD5 switch only. Tests G-AD5-5 (end to end), G-AD5-6 |
| F4 | Medium | Historical feature inputs are not frozen | fixed | `99a2d811c` | **Reproduced:** §7.3 froze only `z_i`, while §7.2 read the audited tuple "where the audit answered", so an audit landing later would change an earlier update on rebuild. The vault keeps only the current revision (`migrations/164_item_snapshots_and_adjudication_fk.sql`, header). **Fix:** §7.5. `item_serve_inputs` (RECEIPT) freezes the served revision's hash, the stamped and resolved features with audit ids, and the signals with receipt ids. Audits record the revision they read, and the canonical audit is the earliest. Historical attempts resolve by the field's graded-revision rule (`field/outcomes.py:154-233`) with `input_status`, and `excluded` never updates. Reinterpretation is a versioned, playbook change. Tests G-AD1-8, G-AD2-16 |
| F5 | Medium | Training excludes failures of the event being forecast | fixed | `99a2d811c` | **Reproduced:** §5.6 excluded primed attempts from the update, while §8.3 scored them as non-successes. So the model learned success given no reveal, and its receipts claimed unconditional unassisted success. **Fix:** §5.3. On a submitted first presentation the binary event is always observed: any help or a reveal during the presentation makes it 0. Censored categories enter the update as `P(Y ≤ 1)`, and revealed correctness is never used. An item exposed before serving (reveal sum at the auto-prime threshold before `served_at`, `attempts/attempts.py:149`, `:1937-1990`) is not served by AD and is excluded from both training and scoring. Skips are right-censored in both, and the estimand says so. A joint help model is deferred with a trigger (§16). Tests G-AD2-14 (simulation with ability-dependent help), G-AD2-17 |
| F6 | Medium | Asynchronous item-only forecasts cannot train their intended signal | fixed | `99a2d811c` | **Reproduced:** §8.2 ran `llm_v1:item` per presentation, asynchronously. §7.3 admits only signals received before a decision, and §5.6 updates on the first attempt per surface only, so on the normal path `z_v1` never entered a factor that could teach `α_v1`. **Fix:** §8.1–8.2. `llm_v1:item` is item-scoped: it runs once per revision when the item is prepared for the pool, plus a one-time backfill, never at presentation. §8.1 separates "valid for scoring" from "informs a decision", which needs receipt before the serve. Test G-AD1-9 |
| F7 | Medium | Outcome categories require hint timing that is not recorded | fixed | `99a2d811c` | **Reproduced:** categories split on help before or after work began, but ordinary hints keep only their count; the field judge is told so (`field/probability_states.py:98-101`), and the practice screen only increments a counter (`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:619`). **Fix:** §5.3. Help timing `h_t` has an explicit `unknown`, never read as "after work"; a success with unknown timing is censored `{0, 1}`. "Help-equivalent" questions use field's own definition (`field/signals.py:217-221`, `:256-259`, `:351-359`). From AD1, `practice_attempts.first_hint_progress` records the screen's existing draft marker (`PracticeScreen.tsx:284-285`) at the first hint (§11.2). Tests G-AD1-10, G-AD2-15 |
| F8 | Low | The implementation handoff is missing | fixed | `99a2d811c` | **Reproduced:** no agent prompt section, and `docs/reviews/adaptive-difficulty-spec.md` did not exist. **Fix:** spec §18 is a per-phase prompt with branch and base, review file, standard rules, prerequisites, paid routes, completion commands and owner-run items. `docs/reviews/adaptive-difficulty-spec.md` records this docs-only stage and separates it from the implementation phases and owner-run measurements |

**The review's "claims that don't hold" all reproduced, and are corrected:**
- **"Latency is used only to size the daily plan" (§3.1).** It also sets value-of-information minutes (`diagnosis/voi_stopping.py:421-449`) and the cost of an unresolved misconception (`scheduling/unresolved_cost.py:10-17`, `:131-145`). §3.1 now lists all three, and that probes log it as an observation feature only (`diagnosis/probe_episodes.py:2551-2560`).
- **Q3 vs §9.5.** §9.5 now maps a unit only by its own facet mapping, and an unmapped unit feeds no target in v1. Spreading over a goal's facets is deferred, because goals do not reference source sets yet (`vault/models.py:136-139`). Q3 says the same.
- **"Replay reproduces history exactly" (§7.3).** Reworded: frozen signals together with §7.5's frozen features are what make replay reproducible (F4).
- **Composed propensities (§10.1).** They are now stated as pair propensities, after the block contract of F2.

**Contradictions found and fixed while checking the revision:**
- **Lanes.** §10.2 said AD ordered the new and push lanes and served repair practice. Under the slot contract, push holds already-attempted items (`daily_plan/lanes.py:23`) and repair holds follow-ups and attempted items (`:9-18`). Neither has a slot, so both are untouched; §6.4 says the same.
- **The commission trigger.** Making draws slot-bound removed the empty-pool commission, since an empty cell has no slot. Under `generation_contract`, the generation path's waypoint pick (`content/authoring/practice_generation.py:383-390`) is now a commission draw.
- **The support.**
  - The slot item could fall out of its own support. It is now always in it while servable, so the kill switch stays exact.
  - Slack is floored at 0.
  - A floor- or override-admitted slot is never replaced by a costlier item (`daily_plan/admission.py:190-201`).
  - With the router off, `π_router = 1`.
- **Certificates.**
  - "The certificate stores `p_req`" assumed a durable table that does not exist. `p_req` now enters the derived certificate's content hash (`goals/certification_cold_probe.py:334`).
  - Probes of a certificate the LO no longer holds stay `certificate_withdrawn`, exactly as today (`:1360-1361`, `:1476-1490`).
  - "The goal's milestone target" made LO certification depend on the goal in view. It now reads every active commitment covering the LO.
- **Level pending.** Without an audit, every existing item would have stayed "level pending" (at most level 1) for good. AD1 now includes an owner-run backfill audit (§7.2). An unresolvable answered revision counts as legacy.
- **§5.3 rows.** A primed attempt with early help matched two rows; primed now takes precedence. "Revealed during" vs "exposed before" is decided by the auto-prime reveal sum, the rule `auto_primed_draft` itself uses.
- **Downstream sections.**
  - §11.2 gains `item_serve_inputs`, `first_hint_progress` (under `forecast_receipts`), the `item_substituted` event (a new kind in `attention_block_events`, migration 096, with no migration needed) and `empty_support`, and renames the feature-credit table.
  - §11.1's AD1 row, §11.3's replay inputs, §1, §4.2, §12, §13, §14's builds, gates and order, and D2, D4 and D7 are aligned.
  - §14's order now says AD2's serve-time receipts need AD1's tables.
- **Citations corrected:**
  - §3.1's bare `:1919`, `:1062`, `:1922` and `:1984` followed `config/schema.py` but meant `practice_generation.py`; they now name the file;
  - `field/signals.py:350` → `:351`;
  - `probe_audit.py:307` → `:311`;
  - `depth_rungs.py:537-545` → `:538-544`;
  - `probe_families.py:455` → `:454` and `:1290-1293` → `:1292-1294`;
  - `daily_plan/engine.py:1931` → `:1925`.

## Gate

| Check | Result |
|---|---|
| Internal consistency | Every bare `§` reference resolves to a heading of this spec (the three others name the storage or probe spec). Gate ids are defined and contiguous: G-AD1-1–10, G-AD2-1–17, G-AD3-1–11, G-AD4-1–11, G-AD5-1–6. D1–D14 are all defined, and no id is used undefined. Stale terms of the superseded contracts (`empty_pool`, rung ledger, `ℓ_req`, `K_c`, component `level`, LO-scope fallback) are absent |
| Code citations | 164 `file:line` citations, continuation citations included, extracted by script: 164 resolve to a unique tracked file with a valid range and 0 are ambiguous or missing. Each cited line was printed and read against its claim; 7 were corrected (above). Symbol citations and the migration head (202) were checked by grep |
| External citations | Unchanged: 121 of 121 verified (appendix §1.2). The fix added none |
| `git diff --check` | Clean, on the working tree and on `4108e1ccd..HEAD` |
| Tests | None run: no code changed |
| Paid calls | None |

Three High findings were fixed, so the stage goes to Codex re-review over `99a2d811c` and this record (implementation goal §2, step 4).
