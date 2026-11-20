# Refactor K2.9–K2.10: extractor choice and ingestion hygiene

Branch `refactor/k2.9-10-extractor-and-hygiene`, base `ece7907885`.
Implements K2.9 and K2.10(a)/(c) from `k2-ingestion-strategy-2026-11-11.md`.
**K2.10(b) stopped at its required comparison; no estimator was changed.**

## Judgment calls to read first

1. `pdf_extractor_for` accepts document bytes and returns `(extractor, consent)` for import jobs.
   Calls without bytes retain their provider-only return value: the unchanged GLM-OCR tests and the
   legacy PDF extraction tool use that API, including `isinstance` and provider methods. The ladder
   is now private `_selected_pdf_extractor` in the same module. There is no proxy or new provider registry.
2. The registry owns the image engine override, local repair refusal, automatic local PDF fallback
   without upload OK, and hosted GLM-OCR consent requirement. `jobs._document_extractor` renders the
   returned requirement with the existing upload-card helper and estimate. The old image and local
   repair sentences moved verbatim, with their comments. The upload permission is passed lazily so
   local readers do not acquire a new vault/config read. Hosted selection returns its requirement even
   after permission is granted: the existing guard still makes its check, in the original order.
3. Native chat routing, Datalab preflight upload checks, effective job config/identity construction,
   scan-without-text cards, and runtime extraction fallback remain where they were. Their ordering and
   hash inputs stay intact. `_image_config` delegates to the registry's `document_pdf_config` so the
   preflight and actual extractor share the image rule. A new document extractor's selection and
   consent policy are confined to the extractor package; no new job branch is required.
4. Conflict resolution uses the existing repository `atomic()` scope, including its `BEGIN IMMEDIATE`
   and nested-savepoint behavior. The conflict read, notation mapping, guarded status update and audit
   append share that scope; the existing store helpers' commits cannot publish a partial resolution.
   `resolve_source_conflict` returns `None` when `WHERE status='open'` matched nothing, without an audit;
   the service reports the existing “already dismissed/resolved” error and rolls back any mapping.
5. The estimator mismatch changes decisions, including sharding at the **default** budget. Unification
   would change model inputs and recorded manifests. It needs a separately authorized behavior change.
6. Two KC1 comments were already corrected at this tip. Rewriting them would add no correction.
   No schema, migration, config key, algorithm tag, model input or identity pin was changed.

## K2.9: choice and consent in one module

`ingest/extractors/__init__.py` now owns `document_pdf_config`, `PdfExtractorConsent` and the
consent-aware `pdf_extractor_for`. The provider ladder moved to `_selected_pdf_extractor` in that
same file. `content/pipeline/jobs.py` supplies runtime settings, bytes and the learner's OK; it translates
unavailable/local-repair requirements or asks the existing upload-card helper to render the requirement.
The requirement retains its flow, plain-import wording, error code and retryability. The existing helper
retains Add's different wording and the upload estimate's pages, cost and page-selection details.

Before production edits, `test_image_without_upload_ok_returns_its_card_requirement` failed with
`TypeError: pdf_extractor_for() got an unexpected keyword argument 'raw_bytes'`.
It now checks the returned extractor and the exact image-card sentence, parameterized over `auto`,
`native`, `marker` and `pypdf` (the three PDF-only choices still select images automatically).
`tests/test_glm_ocr.py` is unchanged. Its runnable consent, repair, refusal and resume cases pass.
The three real-socket cases in it could not run in this sandbox (listed below).

## K2.10(a): atomic, guarded conflict resolution

`content/proposals/conflict_resolution.py` uses one `repository.atomic()` scope.
`db/stores/source_documents.py::resolve_source_conflict` guards the update and appends no audit row
when the guard fails. The service keeps its missing/already-closed error words.
The existing ledger row K2-2 is marked fixed in this worktree. No new out-of-scope bug was found;
the next free K2 id was K2-18, and no new row or strict xfail was needed.

Before production edits, both parameters of `test_conflict_resolution_rolls_back_every_write`
failed because a notation mapping remained after the injected failure:

- `after_mapping`: a patched resolution store raises before the status write;
- `after_status`: a synthetic test-database trigger aborts the audit insert after the status update.

Both now prove no mapping, unchanged complete conflict row, and no audit. The trigger exists only
in the disposable test database; it is not a production schema change.
`test_conflict_resolution_rejects_a_stale_open_read_without_writes` first dismisses a conflict,
then injects the stale open read on a second mapping resolution. Before the change it failed with
`Failed: DID NOT RAISE ConflictResolutionError`; afterward it reports `already dismissed`, and
mapping rows and the complete conflict/audit view stay unchanged. Existing ordinary second-resolution
and successful notation-mapping tests also pass.

## K2.10(b): stopped, with the three current sites established

The old append `_output_tokens` is gone at this tip: append already imports bootstrap's
non-escaping `_result_tokens`. The three current sites are:

| Site | Encoding and estimate | What the number decides |
|---|---|---|
| `source_set_synthesis.py::_shards` | escaping `json.dumps(entry, default=str)`, characters / 4, floor 1 | unit shard membership under `synthesis_shard_input_tokens` |
| `append_neighborhood.py::_estimate_tokens` | escaping JSON, sorted keys, characters / 4, floor 1 | which entity payloads fit, capped flag, and recorded `input_token_estimate` in the neighbourhood manifest |
| `source_set_synthesis.py::_result_tokens`, imported by append | non-escaping JSON, characters / 4, floor 1; dumps a model or accepts a dict | bootstrap output accounting/checks and append `AppendSpend.check_shard_output` against `append_output_tokens` |

Clean-wrapper probes on the **same dict** established the difference before any estimator edit:

| Input | Shard | Neighbourhood | Append/result | Deciding consequence |
|---|---:|---:|---:|---|
| `{"text": "∑漢" * 8}` | 27 | 27 | 7 | two entries make two shards at 40 today; a non-escaping pair fits in 40 |
| `{"text": "∑漢" * 10000}` | 30003 | 30003 | 5003 | two entries make two shards at the default 40000 today; a non-escaping pair fits in 40000 |

The probe called `_shards([x, x], budget)`, `_estimate_tokens(x)` and `_result_tokens(x)`;
it computed the shard's inline estimate using its exact JSON expression. Both probes printed
`non-escaping pair fits ...: True`. Unifying would also admit different neighbourhood contents.
The manifest records that neighbourhood and its estimate. Append is now one reconciliation unit;
it already uses the non-escaping estimator for its output budget. **No unification performed.**

## K2.10(c): the five comments re-located and checked

| KC1 site | Result at this tip |
|---|---|
| `content/proposals/apply_protocol.py`, recovery preamble | already says primary sidecar bind and `doctor --fix-state`; verified the sidecar call, left unchanged |
| `content/facet_identity/judge.py::checkpoint_key` | already explains why this key includes output budget unlike other keys; left unchanged |
| `learnloop_sidecar/handlers/ingest.py`, `BUDGET_BOUNDS` | now names SettingsScreen and OutlineAndPlan as readers via `get_settings`, and IngestActivity's separate bounds |
| `ingest/detect.py::detect_source_kind` | now lists all seven current kinds, including audio and image (the old map said eight; the current `SourceCategory` has seven) |
| `IngestScreen.tsx`, `detectKind` preamble | now cites `learnloop/ingest/resolution.py` as backend classification rather than the nonexistent services module |

Only comments/docstring changed in these three files. A clean-wrapper AST comparison (function
docstrings removed) proved both Python files' executable AST identical to HEAD; removing full-line
comments proved the TypeScript file's non-comment lines identical. No frontend build was needed
for this comment-only edit.

## Commands and results

All project execution used the supplied clean-environment wrappers. `T` means the supplied `t.sh`;
`P` means its sibling `py.sh`. No private configuration, vault, book or fixtures-local directory
was opened; no network or model request was made. Routine source reads and edits are not test commands.
`F` denotes these three exact fail-first node ids:

```text
tests/test_pdf_extractor_selection.py::test_image_without_upload_ok_returns_its_card_requirement
tests/test_exam_readiness_and_conflict.py::test_conflict_resolution_rolls_back_every_write
tests/test_exam_readiness_and_conflict.py::test_conflict_resolution_rejects_a_stale_open_read_without_writes
```

`N` is the following exact 38-file argument list (one chunk, fewer than 40; explicit files, no glob):

```text
tests/test_append_neighborhood_order.py
tests/test_cli_append_units.py
tests/test_cli_ingest.py
tests/test_collection_append_units.py
tests/test_coverage_on_extract.py
tests/test_duration_estimates.py
tests/test_exam_readiness_and_conflict.py
tests/test_facet_identity_ingest.py
tests/test_figure_wait_estimate.py
tests/test_glm_ocr.py
tests/test_graph_nomination_ingest.py
tests/test_ingest_detect.py
tests/test_ingest_fetchers.py
tests/test_ingest_instrument_gates.py
tests/test_ingest_jobs.py
tests/test_ingest_latency_journey.py
tests/test_ingest_m3.py
tests/test_ingest_ownership.py
tests/test_ingest_queue_store.py
tests/test_ingest_runner.py
tests/test_ingest_transcription.py
tests/test_ingest_transcripts.py
tests/test_ingest_vault_switch.py
tests/test_ingestion_checkpoints.py
tests/test_keep_ahead_append_units.py
tests/test_knowledge_map_text_neighbors.py
tests/test_pdf_extraction.py
tests/test_pdf_extractor_selection.py
tests/test_pf_verify_extraction_parity.py
tests/test_probe_episode_conflict_one_check.py
tests/test_rebuild_history_appends.py
tests/test_sidecar_append.py
tests/test_sidecar_ingest_m3.py
tests/test_source_append.py
tests/test_source_ingestion.py
tests/test_source_ingestion_adapters.py
tests/test_source_ingestion_v2lite.py
tests/test_ux_phase1_add_source.py
```

`G` is the exact five-file list `tests/test_identity_pins.py tests/test_retired_config_identities.py
 tests/test_structure_ratchets.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py`.
`K3` is the `-k` expression joining these three exclusions with `and`:
`not test_the_local_backend_renders_pdf_pages_for_a_real_http_server`,
`not test_the_local_backend_reads_an_image_as_one_page`,
`not test_an_unanswering_local_server_is_not_selected`.
`K4` adds `and not test_cli_ingest_runs_canonical_endpoint_and_reports_json`.

| Command | Result line |
|---|---|
| `$T $F -q -n 2` before production edits | `4 failed in 2.15s` (all four expected failures above) |
| `$T tests/test_pdf_extractor_selection.py tests/test_exam_readiness_and_conflict.py -q -n 2` after initial move | `11 passed in 2.47s` |
| `$T tests/test_glm_ocr.py tests/test_pdf_extractor_selection.py tests/test_exam_readiness_and_conflict.py -q -n 2 -m 'not arc_close'` | `1 failed, 122 passed, 2 errors in 9.56s`; all three blocked cases require sockets |
| `$T $N -q -n 2 -m 'not arc_close' -k "$K3"` | `1 failed, 570 passed, 5 warnings in 53.42s`; CLI socket blocked |
| `$T $N -q -n 2 -m 'not arc_close' -k "$K4"` final upload-check ordering | `570 passed, 5 warnings in 52.22s` |
| `$T $G -q -n 2 -m 'not arc_close'` initial | `374 passed in 17.01s` |
| `$T $G -q -n 2 -m 'not arc_close'` final | `374 passed in 17.09s` |
| `$T tests/test_test_layout.py -q -n 1` alone | `3 passed in 19.09s` |
| `$T tests/test_architecture.py -q -n 1` alone | `18 passed in 30.32s` |
| `$P ruff check` (initial and follow-up) | `All checks passed!` both runs |
| `$P lint-imports --no-cache` initial | `Contracts: 43 kept, 0 broken.` |
| `$P ruff check` final | `All checks passed!` |
| `$P lint-imports --no-cache` final | `Contracts: 43 kept, 0 broken.` |
| `$P python -c ...` (two estimator probes described above) | `27 / 27 / 7`, `30003 / 30003 / 5003`; both actual shard counts `2`, both non-escaping pairs fit |
| `$P python` (KC1 AST/non-comment comparison, initial and final) | both Python executable ASTs identical; TypeScript non-comment lines identical |
| `git diff --check` | exit 0, no output |

The five warnings in the name-matched run are the existing Python 3.12 SQLite datetime-adapter
deprecation in `test_source_ingestion_v2lite.py`.

## Size and unverified work

| Step | Production added/deleted | Production net | Test net | Step net excluding this shared record |
|---|---:|---:|---:|---:|
| K2.9 | 92 / 58 (150 changed) | +34 | +15 | +49 |
| K2.10(a) | 46 / 39 (85 changed) | +7 | +59 | +66 (ledger row 1 / 1, net 0) |
| K2.10(b) | 0 / 0 | 0 | 0 | 0, stopped |
| K2.10(c) | 5 / 3 (8 changed; comments/docstring only) | +2 | 0 | +2 |
| K2.10 total | 51 / 42 (93 changed) | +9 | +59 | +68 |

Both steps remain below about 200 changed production lines. Combined before this shared record:
218 added, 101 deleted; net +117. This shared record adds 223 lines, for net +340 overall.
No pin or pin helper was edited. `CLAUDE.md`, `refactor-status.md`, generated vault references and the
index are unchanged; nothing was staged or committed.

These four cases could not run because creating an AF_INET socket raises sandbox `PermissionError`:

- `tests/test_glm_ocr.py::test_the_local_backend_renders_pdf_pages_for_a_real_http_server`;
- `tests/test_glm_ocr.py::test_the_local_backend_reads_an_image_as_one_page`;
- `tests/test_glm_ocr.py::test_an_unanswering_local_server_is_not_selected`;
- `tests/test_cli_ingest.py::test_cli_ingest_runs_canonical_endpoint_and_reports_json`.

The final run deselects only those four cases. Neither of those two files is counted as a complete
passing file; their other tests ran. The other 36 name-matched files ran completely under the requested
`not arc_close` marker. No full suite, arc-close/fresh-connections run, separate durability lane,
private-vault replay/shadow, live provider, model call, frontend build or vault-reference generation
was performed. K2.10(b) remains intentionally incomplete under the explicit stop rule.
