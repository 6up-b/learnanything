# UX-42: keep creates whose model omitted IDs

Status: fixed in the working tree of `fix/ux42-create-without-id`, not yet committed or landed.
Base: `c9e123623e`. Implementation and verification follow the pre-code findings below.

## Measurement supplied by the walk

The first two topics of a finished section each returned three grounded practice-item
creates, audited `passed`, marked `auto_apply`, with both `proposed_entity_id` and
`payload.id` null. The target validator rejected the entire answer. One JSON repair
returned byte-identical text (18,534 characters), then failed after about three minutes
and 9,000 output tokens per topic, leaving no questions. Other calls supplying `pi_`
slug IDs applied successfully. This task uses that field-value report, not private data.

## Step 0 — recorded before code

`AuthoringProposalItem.coerce_payload_by_item_type` selects and validates the payload
before `validate_target_rules`. The required-create-ID rule covers learning objects,
practice items, concepts and error types. Concept edges and rubrics are exempt.

| Type | Named IDs and existing minting conventions |
|---|---|
| learning_object | `lo_<snake slug>`; synthesis `normalize._slug("lo", title, fallback)` and `unique` |
| practice_item | `pi_<snake slug>`; synthesis `_slug("pi", prompt prefix, fallback)`; learner/exercise authoring also uses `pi_learner_<ulid>` / `pi_exercise_<ulid>` |
| concept | `concept_<snake slug>` in synthesis; existing registry IDs also use bare names; synthesis `_slug("concept", title, fallback)` |
| error_type | Semantic vocabulary such as `retrieval_failure` and `sign_convention_slip`; diagnosis copies the attributed type as ID. No generic anonymous-entity minting helper. Leave unnamed error types failing rather than invent a new taxonomy convention. |
| concept_edge | Exempt: `_default_edge_id` in proposals/patches derives `edge_<source>_<relation>_<target>`; synthesis uses `edge_<relation>__<source>__<target>` with `unique` |
| rubric | Exempt: attached to `target_practice_item_id`, no independent entity ID |

Facets and blueprints are not AuthoringProposal item types: synthesis uses
`facet_<claim slug>` and `bp_<fallback>`. The shared `ids.snake_case` helper normalizes
slugs; synthesis's local `unique` selects the first free `_2`, `_3`, … suffix.
Its random ULID fallback is unsuitable for replaying an unnamed answer.
Vault entity model IDs are strings, with no additional prefix regex in these models;
minted names must remain safe as filename components and follow the existing prefixes.

Readers: `_has_id_collision` checks learning objects, practice items and edges;
`proposal_item_row` copies proposed IDs into a missing payload ID, then validates and
routes the row. Available-concept/learning-object sets and edge validation read them
for intra-proposal references. Apply compiles and writes the payload ID. Source ingestion's
`merge_window_proposals` deduplicates on proposed ID (else type/operation/client ID).
The sidecar constructs named IDs for explicit edits; graph edit proposals also name IDs.
Thus generated IDs must be deterministic, distinct even for repeated client IDs,
reserved against all named proposal IDs and existing vault IDs, and unchanged on replay.
UX-37 stores both a paid answer and a prepared part (including row IDs) before apply;
the prepared-part receipt is what makes crash-after-apply resume apply nothing twice.

The plan provider's wire repair currently sends `_JSON_ONLY`, then the instruction
“Repair the following model output into a JSON object that validates against this
JSON schema. Return only JSON.”, the sorted JSON schema, the rejected text, and the
original output-budget sentence when present. It keeps deadline/effort/budget, is tool
free, and does not send the validation exception or original workspace. Nullable IDs
satisfy the schema, while the Python validator imposes a rule absent from that schema.
The code therefore gives no diagnosis requiring a different answer; it cannot establish
why a particular model repeated the text. Smallest correction: include the first
validation error only in the repair prompt, with no change to the first request/schema.

## Judgment calls and intended rule

Mint at `AuthoringProposal` validation, before item coercion/target validation. Preserve
any nonblank model ID verbatim. Use the supported type prefix, an ASCII snake slug of
the client ID, and an answer-derived hash including item content and ordinal. Reserve
named IDs first, then choose first-free `_2`, `_3`, … suffixes in answer order.
The authoring request supplies existing vault IDs through a local validation scope,
without adding anything to the prompt or wire model; standalone parsers can supply
validation context. Checkpoints persist the resolved IDs and never remint named IDs.

An unavoidable distinction: the candidate is a function of the answer alone; choosing
a free name in an arbitrary occupied vault necessarily also depends on the occupied
set. Same answer plus same reservations gives the same resolution. Checkpoint replay
keeps the resolved ID even after apply makes it occupied. There is no mathematically
possible answer-only function guaranteed to avoid an arbitrary vault's contents.

Unnamed error types remain refused; edges/rubrics keep their existing exempt behavior.
Named-ID conflicts and other validation/grounding/audit errors keep existing behavior.

## Fail first (unchanged production)

`t.sh tests/test_authoring_create_ids.py -q -n 2`: initial baseline-capture run
**11 failed, 1 passed in 3.53s**. One failure deliberately captured the existing
recorded-answer row digest; it is not defect evidence. With that digest pinned and
still no production edits, the same command gave **10 failed, 2 passed in 3.59s**.

The three-create section fails with `AIInvalidOutput` after repair; crash/replay sees
zero applied IDs; null IDs fail the target validator; empty/whitespace IDs stay
nonunique; the named reservation and occupied-vault cases fail on missing IDs;
learning-object/concept creates also fail the target validator. The repair regression
fails because the actual second request lacks `value must be positive`. The recorded
named-answer row digest and unnamed error-type refusal are preservation controls:
they correctly pass before the fix, rather than being artificially made to fail.

## Implementation and scope

`content/proposals/create_ids.py` implements normalization; the before-validator on
`AuthoringProposal` invokes it before validating any `AuthoringProposalItem`.
For learning objects, practice items and concepts, both IDs being absent, null,
empty or whitespace-only triggers minting. The forms are respectively
`lo_<client-slug>_<digest>`, `pi_<client-slug>_<digest>` and
`concept_<client-slug>_<digest>`. The slug uses `ids.snake_case`, keeps ASCII only,
clips to 40 characters and falls back to `unnamed`. The digest is the first 20
hexadecimal characters of SHA-256 over compact, sorted-key UTF-8 JSON of
`[zero_based_item_ordinal, raw_item]`. The raw item includes type, client ID,
payload, audit and other fields. Repeated or identical client items are distinct
because their ordinals differ. Input dictionaries are copied, not mutated.

Before minting, reserve both ID fields of every named item (including later items),
then reserve existing vault IDs. On collision try `_2`, `_3`, … in ascending order;
reserve each result before the next item. No randomness, wall clock, request ID,
proposal database ID or local path contributes to the candidate. A nonblank named
ID is never normalized, renamed or rewritten. Its existing collision refusal is
also unchanged. `payload.id` becomes null only for a create whose two IDs were
blank, so the existing row-copy operation inserts the minted proposed ID.

A context-local, exception-safe reservation scope surrounds authoring requests,
canonical-ingest requests and CLI file parsing. Vault IDs are read lazily only
when an answer actually has an unnamed supported create, so named-answer paths
keep their old reads and row bytes. It reserves learning objects, practice items,
concepts, error types, facets and edges from the full vault, not a prompt's subject
subset. Independent callers of `AuthoringProposal.model_validate` can pass
`context={"existing_entity_ids": ...}` or use the same reservation scope. A parser
with no vault cannot reserve that vault; callers supplying already-validated
objects must reserve at parsing, not after serialization has made the minted name
indistinguishable from a deliberately named one. No ID-origin field is added to
saved data or the schema.

The paid-answer checkpoint stores the resolved IDs. Its load path sees named IDs
and preserves them even when apply has since occupied them. The existing prepared
part receipt preserves row IDs and acceptance decisions across crash-after-apply.
No apply protocol, duplicate-prompt rule, grounding rule or review policy changes.
Concurrent writers can still invalidate an earlier vault snapshot; existing apply
conflict protection remains authoritative. This is not a new atomic allocator.

Error types without IDs still fail the required-ID validator: their IDs name the
semantic taxonomy, and this patch does not invent a generic prefix or vocabulary.
Concept edges and rubrics retain existing derivation/attachment behavior. Updates,
deactivations, malformed payloads and other invalid creates remain subject to the
old validators. Direct standalone `AuthoringProposalItem` validation retains its
required-ID rule; normalization belongs to the enclosing answer boundary.

The plan repair now includes `Validation error:` and the first caught validation
exception before the schema/output. Only the repair turn's text changes. Its call
count, budget, deadline, effort, tool-free nature and first request remain unchanged.
No prompt template/version, wire-schema field, configuration, migration or algorithm
tag changes, and no pins are regenerated.

## Additional entry-point regression

After the common parser fix, but before changing either entry point:
`t.sh tests/test_authoring_create_ids.py -q -n 2 -k other_wire_entry_points`
gave **2 failed in 2.30s**. Both canonical ingestion and file import reused the
occupied candidate instead of selecting `_2`. Their wrappers now supply the same
lazy reservations to the common parser. There is no second minting implementation.

## Working-tree base

The supplied source base is `c9e123623e`; the actual checkout HEAD is `c7572bda76`,
whose sole difference is the already-committed generated-reference manifest. No
source difference affects the before/after comparison. This task did not change
that manifest or any generated vault reference.

## Final regression coverage and verification log

The final test file also checks repeated/identical client items receive distinct IDs,
and tests the recorded answer with its ID owned by the proposed field, the payload,
or both. The exact recorded output is read from the existing
`tests/fixtures/diagnosis_journey_golden.json`; the whole serialized row list, with
only row ULID and time fixed, has the pre-fix SHA-256
`88222adcb3f52df301850e4adab6fc8f850a214d924e233e6135291a95f9389a`.
No existing recorded answer or golden was edited.

A final unchanged-production check saved all five edited existing production files,
replaced their contents with `git show HEAD:<file>`, ran the new test file, and
restored working contents in `finally` without touching the index. The new helper
was unreachable from the original production files. First run: **14 failed,
4 passed in 3.48s**, including a proposed malformed-type preservation assertion
that exposed an unrelated existing `TypeError`. That assertion was removed rather
than changing unrelated validation. Next run: **13 failed, 4 passed in 3.63s**.
An extra apply test for duplicate client IDs then exposed the existing persistence
guard `proposal contains duplicate client_item_id values`. That guard protects
dependency references and is unchanged; the requested allocation test still proves
the generated entity IDs are distinct and safe. The extra apply assertion was
removed instead of renaming client IDs or weakening persistence. Definitive final-file
run: **12 failed, 4 passed in 3.51s**. All 12 intended behavior regressions fail on
unchanged production; the three named-ID ownership controls and error-taxonomy
control pass there. Duplicate-client proposals still fail at persistence, for their
client keys rather than entity-ID collisions.

`t.sh` and `py.sh` below mean the supplied isolated wrappers. All pytest commands
use explicit files and at most two workers; no whole-suite invocation is used.

| Command | Result |
|---|---|
| `t.sh tests/test_authoring_create_ids.py -q -n 2` (baseline capture) | 11 failed, 1 passed in 3.53s; one failure captures the pre-fix row digest |
| Same, baseline pinned, before production edits | 10 failed, 2 passed in 3.59s |
| `t.sh tests/test_authoring_create_ids.py tests/test_section_question_parts.py tests/test_identity_pins.py -q -n 2` | 373 passed in 50.66s |
| `t.sh tests/test_authoring_create_ids.py -q -n 2 -k other_wire_entry_points` (before entry-point scopes) | 2 failed in 2.30s |
| `t.sh tests/test_authoring_create_ids.py -q -n 2` (after scopes) | 14 passed in 3.65s |
| Same command, unchanged-production rechecks (temporary script via `py.sh python`) | 14 failed, 4 passed in 3.48s; 13 failed, 4 passed in 3.63s; final 12 failed, 4 passed in 3.51s after removing the two out-of-scope assertions |
| `py.sh ruff check` | All checks passed! |
| `py.sh lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| `git diff --check` | exit 0, no output |

The requested filename selection has 32 files. With the three required section/Today
files appended it is one 35-file chunk, under the 40-file cap:

```sh
t.sh tests/test_authoring_context.py tests/test_authoring_contract.py tests/test_authoring_create_ids.py tests/test_exercise_authoring.py tests/test_family_proposals.py tests/test_graph_edit_proposals.py tests/test_item_authoring.py tests/test_learner_pick_proposal.py tests/test_practice_proposal_caller_columns.py tests/test_probe_proposal_reads.py tests/test_proposal_dependencies.py tests/test_proposal_impressions.py tests/test_proposal_persistence.py tests/test_proposal_review_policy.py tests/test_reader_authoring.py tests/test_rerun_proposals.py tests/test_sidecar_item_authoring.py tests/test_sidecar_synthesis.py tests/test_source_ingestion.py tests/test_source_ingestion_adapters.py tests/test_source_ingestion_v2lite.py tests/test_source_set_synthesis.py tests/test_synthesis_answer_reuse.py tests/test_synthesis_criterion_dependencies.py tests/test_synthesis_eval.py tests/test_synthesis_gates.py tests/test_synthesis_identifiability.py tests/test_synthesis_manifests.py tests/test_synthesis_runs_repo.py tests/test_synthesis_sweep_primary_only.py tests/test_synthesis_tail_golden.py tests/test_ux_phase2_error_type_proposals.py tests/test_section_question_parts.py tests/test_first_questions_today.py tests/test_first_questions_arrive.py -q -n 2 -m 'not arc_close'
```

Initial result: **1 failed, 414 passed, 5 warnings in 73.69s**. The sole failure is
`tests/test_first_questions_arrive.py::test_the_plan_route_request_is_byte_identical_under_a_ceiling`,
which cannot open its local fake HTTP socket (`PermissionError: Operation not permitted`).
It is not counted as verified. Warnings are existing SQLite datetime-adapter deprecations.

Safeguards and every final added test:

```sh
t.sh tests/test_authoring_create_ids.py tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py -q -n 2 -m 'not arc_close'
```

Initial result: **1 failed, 738 passed in 33.74s**; the extra duplicate-client apply
assertion hit the existing persistence guard, as explained above. After removing
that assertion, final result: **738 passed in 33.18s**. This includes all 16 final
new tests, unchanged identity pins and diagnosis goldens. No regeneration occurred.

Final `py.sh ruff check`: **All checks passed!** Final
`py.sh lint-imports --no-cache`: **Contracts: 43 kept, 0 broken.**

Final rerun of the same 35-file command: **1 failed, 416 passed, 5 warnings in
72.65s**. Only the same socket-opening test failed; it remains unverified.

## Unverified and handoff limits

No real-provider call, network call, private configuration/vault read or live-route
walk was performed. The supplied latency/token measurement is not remeasured.
The response stub runs the real plan provider's parser/repair control flow but
replaces `_respond`, so its request counter counts provider turns without sockets.
Real HTTP delivery, provider behavior, UI rendering, concurrent-writer races and
live token/latency savings are not verified. The existing socket test named above
could not run and is excluded from verified results.

All changes are uncommitted for the orchestrator. No `git add`, `git commit`, landing
gate, reference regeneration, `CLAUDE.md` edit or `refactor-status.md` edit occurred.
The new source/helper, test and review record remain untracked until the orchestrator
stages them; include those files along with the tracked diff.

## Isolated checks and size

Each of these ran alone, after all other pytest processes finished:

```sh
t.sh tests/test_test_layout.py -q -n 1
```

**3 passed in 20.18s.**

```sh
t.sh tests/test_architecture.py -q -n 1
```

**18 passed in 32.02s.** Final `git diff --check`: **exit 0, no output**.

Production: **+119 / -20, net +99 lines, six files**. All changes, including
this record, the ledger and tests: **+626 / -20, net +606
lines, nine files** (including the three new files, which `git diff --stat` alone
omits until staging). Nothing remains to implement for the missing-ID defect;
the stated unchanged guards, socket limitation and real-route verification remain.
