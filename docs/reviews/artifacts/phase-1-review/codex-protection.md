FINDINGS

1. HIGH — Restoring an empty file makes an unsafe loaded snapshot pass the gate

Where: src/learnloop/content/sources/exam_material.py:993–1003, 1031; src/learnloop/vault/loader.py:330. Retained by K1-1, 885f875096.

Scenario: Load a vault while source_sets.yaml is empty, then restore its valid exam membership without reloading that LoadedVault. The empty load has no loader issue. protection_issues checks the restored file, returns no problems, and exam_material reads the snapshot’s empty source_sets. Exam-only membership disappears from protection. The gate must validate the snapshot it actually uses, or require its reload.

Why tests missed it: test_k1_source_sets_gate.py leaves each corruption in place throughout the read.

Smallest failing test: Save valid exam YAML; empty it; load the vault; restore the YAML; call exam_material with the old vault. Assert that it refuses or still protects the exam extraction.

Confidence: certain for the predicate. I did not execute the desktop reload journey.

2. HIGH — The Reader still passes an empty list when its config disappears

Where: src/learnloop/content/pipeline/jobs.py:2963–2964, 5625, 5632–5634; src/learnloop/reader/reader_requests.py:584, 607. Missed by 885f875096.

Scenario: A running Reader worker has cached its model client. A queued preset concerns an unmarked reading of a book protected by an exam scope in source_sets.yaml. If learnloop.toml disappears before draining, _reader_source_sets returns [], bypassing _require_readable. The source-set scope vanishes from the held-out partition and the reading’s blocks reach the synthesis model. Missing configuration must refuse the request, not mean “no source sets.”

Why tests missed it: The corruption fixtures retain learnloop.toml and exercise the normal vault-returning branch.

Smallest failing test: Create the scoped book and unmarked reading, queue a preset, provide a cached fake client, remove learnloop.toml, then drain. Assert no model call and a protection refusal.

Confidence: certain from the call path; not executed.

3. HIGH — Concurrent source-set saves can silently erase exam protection

Where: src/learnloop/vault/writer.py:441–463; src/learnloop/cli/source_set.py:20, 62, 83.

Scenario: Two writers read the same source_sets.yaml. Writer A adds an exam member; writer B updates another set’s title. A commits, then B replaces the entire file using its earlier snapshot, erasing A’s membership. The resulting YAML is valid, so the gate accepts it and the exam becomes ordinary source material. Atomic replacement prevents torn files but does not serialize read-modify-write operations. The CLI calls this writer without a vault mutation lock.

Why tests missed it: K1-1 tests a failed rename and a single-writer round trip, not concurrent updates.

Smallest failing test: Interleave two upserts after both have read the file, targeting different sets. Complete the exam update first. Assert both updates survive and the exam extraction remains protected.

Confidence: certain for this interleaving; no concurrency test executed. The race predates the range and remains after 885f875096.

4. HIGH — MCP filters protected passages after sending them to its verification model

Where: src/learnloop/remote/sources.py:184–195; src/learnloop/source_retrieval/find_sources.py:752–782, 584–605. Incomplete K1-4 fix, d660d565c2.

Scenario: An exam-reserved item or diagnostic probe cites an otherwise ordinary textbook passage. MCP find_sources searches that passage with verify=true. The initial withheld_items check only checks availability. Retrieval’s pre-verification filter removes exam-classified spans, but not this item’s reserved/probe passages. _verify sends their text to the model; _shown removes them only afterward. The same late filtering affects solution and assessment-lane passages that are not exam-classified.

Why tests missed it: test_k1_mcp_find_sources.py calls _shown directly with fabricated hits, bypassing retrieval and verification.

Smallest failing test: Call find_passages with verify=true, a reserved item’s source passage, and a recording fake verifier. Assert the protected text never enters its prompt.

Confidence: certain from the call ordering; no provider or test executed.

5. HIGH — The remediation fix still lets ordinary due practice spoil the cold item

Where: src/learnloop/scheduling/serving_exclusions.py:112–128, 326–331; src/learnloop/scheduling/scheduler.py:275, 457. Incomplete K1-6 fix, 742308f515.

Scenario: A treatment episode selects an active, ordinarily due item as cold_item_id, before creating its cold_retry task. The new reservation enters only out_of_timing_serving_exclusions. The routine due queue uses routine_serving_exclusions, which never reads it. Consequently, ordinary scheduled practice can still offer the item before its check—the journey the fix record says was corrected.

Why tests missed it: The new test checks cold_administration_open and the out-of-timing set, never build_due_queue.

Smallest failing test: Establish that an ordinary due item appears in build_due_queue; create a treatment episode reserving it without a task; rebuild and assert that it no longer appears as ordinary practice.

Confidence: certain about the missing exclusion; the full queue fixture was not executed.

6. HIGH — Expired cold retries leave reservations with no automatic release

Where: src/learnloop/db/repositories.py:4118–4120, 4195–4205; src/learnloop/diagnosis/remediation.py:1093–1098, 1470; src/learnloop/instructional/policy.py:46. Newly affects serving and tutoring through 742308f515.

Scenario: A cold_scheduled episode’s retry expires unanswered. Expiry changes only the task; the episode remains cold_scheduled with its cold_item_id. The new query continues reserving that item indefinitely. find_practice and quick-check admission exclude it, and tutoring still treats it as a cold administration. Withdrawal has the same problem when no replacement is scheduled. A terminal retry needs to release or explicitly transfer its reservation.

Why tests missed it: Tests directly construct completed and abandoned episodes. They never let a real retry expire or be withdrawn.

Smallest failing test: Create an episode and linked retry, advance beyond expires_at, run normal expiry processing, and assert cold_administration_open is false and practice admission no longer reserves the item.

Confidence: certain from the lifecycle writes; expiry processing was not executed.

7. MEDIUM — Atomic saves sever a symlinked source-set file

Where: src/learnloop/vault/yaml_io.py:111–117; src/learnloop/vault/writer.py:463. Introduced by 885f875096.

Scenario: sources/source_sets.yaml is a symlink to a shared or separately managed file. Loading and the former write_yaml follow that link. The new writer creates its temporary beside the link and replaces the link itself, leaving the target unchanged. The vault silently becomes a detached copy; subsequent protection edits to the shared target no longer reach it. File symlinks are explicitly supported by the loader’s fingerprinting at vault/loader.py:138–143.

Why tests missed it: Both atomic-write tests use ordinary destination files.

Smallest failing test: Upsert through a symlinked source_sets.yaml. Assert the link remains and its target contains the update.

Confidence: certain from os.replace semantics; no filesystem experiment executed.

8. MEDIUM — The router boundary pin hashes a test reconstruction instead of the production identity

Where: tests/identity_pins_helpers.py:820–843; src/learnloop/daily_plan/objective_chooser.py:1422–1439; src/learnloop/daily_plan/types.py:163–175. Introduced by e1884dd311.

Scenario: A refactor changes BlockCandidate.log_row’s serialized fields or the production boundary assembly. Production cache keys and numeric seeds change, but C3’s pin continues hashing its independent literal. Its support row contains only candidate_id and lane, whereas production includes item IDs, reading, timing, value and optional annotations. Shape pins cannot detect a serialization-only change.

Why tests missed it: C3 invokes production hashing and numeric_seed, but never the production assembly or log_row. The AST check does not follow that cross-function flow.

Smallest failing test: Change log_row through a test seam so production support gains an identity-bearing value; assert C3’s computed boundary pin changes. It currently remains unchanged. Pin a boundary captured from the actual chooser path.

Confidence: certain about the coverage gap. I did not demonstrate an actual production identity drift in this range.

CHECKED AND FOUND SOUND

Shared reader call search: direct production calls found use vaults; resolver production callers supply exam_source_sets=vault. The unsafe remaining list branch is finding 2.

K1-1: persistent parse/schema corruption and a still-empty file cause the shared readers to refuse; phone_media and adaptive-difficulty protection withhold on exceptions.

K1-3: the session reservation check precedes the held-out switch; the exam handler uses its separate serving path.

K1-4: the final MCP response filter covers probes, effective solution roles and assessment-lane passages; its earlier model exposure is finding 4.

K1-5: the inspector hides hints in both modes when answeringItemId matches. The documented payload exposure remains outside this UI fix.

K1-9: the exception message contains no loader/file contents; direct sidecar and MCP catches preserve its code; phone translation returns a non-retryable 409.

D-2: added known types come from the same version-dependent builtin vocabulary as grading validation.

D-7: the revised message branches on material-view availability, not whether protected material actually exists.

Atomic writing: temporary placement and file-fsync → replace → directory-fsync ordering are present for ordinary destinations.

RETIRED_FIELDS: identity_view restores retired values before selecting fields and raises for missing named fields; no additional removal-induced identity change was established.

COULD NOT CHECK

No tests, application processes, network calls or writes were performed. Proposed failing tests are unexecuted.

Actual crash durability, filesystem-specific rename/fsync behavior, deployed file permissions, and occurrence of concurrent saves require controlled execution.

Live vaults, historical remediation episodes, desktop navigation/reload timing, and end-to-end phone/MCP rendering were not inspected.

The identity review establishes the C3 test gap; it does not prove byte-for-byte stability of every compared identity across all configurations.