---
title: "learnloop.cli.app"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/app.py"
source_paths:
  - "src/learnloop/cli/app.py"
source_commit: "903b93e7e8ac75c12240a78a0ac5f785c300a6d6"
source_commit_timestamp: "2026-11-09T14:22:36-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.app module"
  - "src/learnloop/cli/app.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.app`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps app behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `init`, `upgrade`, `add_subject`, `add_note`, `ingest`, `ingest_exam`, `import_sources`, `quick_add_cmd` and 78 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/app.py](../../../../../../src/learnloop/cli/app.py) |
| Source lines | 5572 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `903b93e7e8ac75c12240a78a0ac5f785c300a6d6` |
| Commit timestamp | `2026-11-09T14:22:36-05:00` |

## Public API

- `init(path: Annotated[Path, typer.Argument(help='Vault directory to create.')]=Path('.'), force: Annotated[bool, typer.Option('--force', help='Allow scaffolding inside a populated directory that is not already a vault.')]=False, subject: Annotated[str | None, typer.Option('--subject', help='Optional first subject title to seed.')]=None, starting_level: Annotated[str | None, typer.Option('--starting-level', help='Optional learner level: new_to_this, some_exposure, comfortable, or strong_background.')]=None, level_note: Annotated[str | None, typer.Option('--level-note', help='Optional note accompanying --starting-level.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 68)
- `upgrade(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, to: Annotated[str, typer.Option('--to', help=f'Target algorithm version (mvp-0.7, mvp-0.8, mvp-0.9, mvp-0.10, mvp-0.11, mvp-0.12, mvp-0.13, mvp-0.14, mvp-0.15, mvp-0.16, mvp-0.17, mvp-0.18, mvp-0.19, mvp-0.20, mvp-0.21, mvp-0.22, mvp-0.23, mvp-0.24, mvp-0.25, mvp-0.26, mvp-0.27, mvp-0.29, mvp-0.30, {WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION}, {READING_PATH_PLAN_ALGORITHM_VERSION}, {CLAIM_FIXES_ALGORITHM_VERSION}, {REPLAY_LEDGER_ALGORITHM_VERSION}, {ONE_ASK_ALGORITHM_VERSION}, {SUPERSEDED_CLAIMS_ALGORITHM_VERSION}, {ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION}, {COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION}, {READER_FOLLOWUPS_ALGORITHM_VERSION}, {DELIVERABLE_PLAN_ALGORITHM_VERSION}, {TEACHER_ALGORITHM_VERSION}, {HELP_FOLD_ATTACH_ALGORITHM_VERSION}, {LESSON_SUGGESTIONS_ALGORITHM_VERSION}, {DATA_CAPTURE_ALGORITHM_VERSION}, {FOLLOWUP_SERVE_ALGORITHM_VERSION}, {INTERVAL_FACTOR_ALGORITHM_VERSION}, {ROUTER_OBJECTIVE_ALGORITHM_VERSION}, {ROUTER_CALIBRATION_ALGORITHM_VERSION}, {ROUTER_LEARNED_TAIL_ALGORITHM_VERSION}, {ROUTER_FOLLOWUPS_ALGORITHM_VERSION}, {TEACHER_PROBES_ALGORITHM_VERSION}, {LESSON_OPPORTUNITY_ALGORITHM_VERSION}, {LESSON_OFFERS_ALGORITHM_VERSION}, {PHONE_PROBES_ALGORITHM_VERSION} or {FAILURE_SHARE_ALGORITHM_VERSION}); default: the latest.')]=LATEST_ALGORITHM_VERSION) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 109) — Atomically activate a knowledge-model version for this vault.
- `add_subject(subject_id: Annotated[str, typer.Argument(help='Kebab-case subject id.')], title: Annotated[str, typer.Argument(help='Display title.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 566)
- `add_note(subject_id: Annotated[str, typer.Argument(help='Subject id.')], note_id: Annotated[str, typer.Argument(help='Note id, with or without note_ prefix.')], title: Annotated[str, typer.Argument(help='Note title.')], body: Annotated[str, typer.Option('--body', help='Inline note body.')]='', file: Annotated[Path | None, typer.Option('--file', help='Markdown file to use as note body.')]=None, source_type: Annotated[str, typer.Option('--source-type', help='Source type: learner_note, canonical_source, or imported.')]='learner_note', related_los: Annotated[str | None, typer.Option('--related-los', help='Comma-separated learning object ids to link this note to.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 575)
- `ingest(source: Annotated[str, typer.Argument(help='URL or local source file to ingest.')], kind: Annotated[str, typer.Option('--kind', help='Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter.')]='auto', subject: Annotated[str | None, typer.Option('--subject', help='Target subject id.')]=None, learning_objects: Annotated[list[str] | None, typer.Option('--learning-object', help='Existing Learning Object anchor. Can be repeated.')]=None, goal: Annotated[str | None, typer.Option('--goal', help='Active goal id to link ingested concepts to.')]=None, allow_auto_captions: Annotated[bool | None, typer.Option('--allow-auto-captions', help='Allow generated YouTube captions when human captions are unavailable.')]=None, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra canonical-ingestor instructions.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for ingestion.')]=None, pdf_engine: Annotated[str | None, typer.Option('--pdf-engine', help='PDF extraction engine override: auto, glm_ocr, marker, or pypdf.')]=None, pdf_llm: Annotated[bool | None, typer.Option('--pdf-llm/--no-pdf-llm', help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf]).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, progress_json: Annotated[bool, typer.Option('--progress-json', hidden=True)]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 610)
- `ingest_exam(source: Annotated[str, typer.Argument(help='URL or local past-exam file to ingest.')], kind: Annotated[str, typer.Option('--kind', help='Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter.')]='auto', subject: Annotated[str | None, typer.Option('--subject', help='Target subject id.')]=None, goal: Annotated[str | None, typer.Option('--goal', help='Active goal id to link ingested concepts to.')]=None, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra instructions appended to the exam-ingest instructions.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for ingestion.')]=None, pdf_engine: Annotated[str | None, typer.Option('--pdf-engine', help='PDF extraction engine override: auto, glm_ocr, marker, or pypdf.')]=None, pdf_llm: Annotated[bool | None, typer.Option('--pdf-llm/--no-pdf-llm', help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf]).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, progress_json: Annotated[bool, typer.Option('--progress-json', hidden=True)]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 661) — Ingest a past practice exam: one tagged practice item per exam question.
- `import_sources(sources: Annotated[list[str], typer.Argument(help='URLs, arXiv ids, or local files to import.')], subject: Annotated[str | None, typer.Option('--subject', help='Optional subject id for the batch.')]=None, inventory: Annotated[bool, typer.Option('--inventory', help='Also queue role-specific unit inventories.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the durable batch as JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 722) — Import sources into the vault library through the durable queue (§6.1).
- `quick_add_cmd(source: Annotated[str, typer.Argument(help='URL or local file to turn into a study map.')], subject: Annotated[str | None, typer.Option('--subject', help='Target subject id for the study map.')]=None, yes: Annotated[bool, typer.Option('--yes', '-y', help='Skip the single confirmation prompt.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 759) — Quick add (§1): paste one source -> auto-selected units, suggested role, default brief, ONE confirmation, then a priority build batch to a study map.
- `backfill_originals_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 832) — Copy revision originals into the managed store (canonical-sources/raw/).
- `source_outline_command(ref: Annotated[str, typer.Argument(help='Extraction, revision, or artifact id to outline.')], json_output: Annotated[bool, typer.Option('--json', help='Emit the outline as JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 861) — Deterministic outline of a source's extraction — zero agent runs (§3/§5.7).
- `select_units_command(extraction_id: Annotated[str, typer.Argument(help='Extraction id to record a selection for.')], units: Annotated[list[str], typer.Option('--unit', help='Selected unit id (repeatable).')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the stored selection as JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 890) — Persist a per-extraction unit selection (§5.3).
- `inventory_command(ref: Annotated[str, typer.Argument(help='Revision / extraction / artifact id.')], units: Annotated[list[str] | None, typer.Option('--unit', help='Unit id to inventory (repeatable).')]=None, role: Annotated[str, typer.Option('--role', help='Confirmed role (§4.2).')]='reference', profile: Annotated[str | None, typer.Option('--profile', help='semantic|practice|assessment|combined.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for inventory.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 912) — Run role-aware unit inventories over selected units (§7).
- `source_coverage_command(set_id: Annotated[str, typer.Argument(help='Source-set id.')], json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 968) — Deterministic coverage + readiness preview for a collection (§9.3).
- `synthesize_command(set_id: Annotated[str, typer.Argument(help='Source-set id.')], mode: Annotated[str, typer.Option('--mode', help='auto|bootstrap|append.')]='auto', brief_file: Annotated[Path | None, typer.Option('--brief-file', help='JSON synthesis brief (§8.3).')]=None, apply_map: Annotated[bool, typer.Option('--apply', help='Accept the study map under the vault lock (requires mvp-0.7).')]=False, create_goal: Annotated[bool, typer.Option('--create-goal', help='Create an exam-prep Goal wired to the minted facets.')]=False, new_revision: Annotated[list[str] | None, typer.Option('--new-revision', help='Revision id(s) newly added/changed (append mode).')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for synthesis.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help="Plan the run's graph-nomination embedding spend; no model or embedding client, no data changes.")]=False, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1036) — Create or UPDATE a study map from a source set (§8 bootstrap / §10 append).
- `synthesize_repair_command(run_id: Annotated[str, typer.Argument(help='Failed synthesis run id with a preserved candidate.')], ops_file: Annotated[Path | None, typer.Option('--ops-file', help='JSON list of explicit repair ops (drop_dependency / remap_dependency).')]=None, no_auto: Annotated[bool, typer.Option('--no-auto', help='Skip auto-derived repairs; apply only --ops-file.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show stored diagnostics and derived ops without revalidating.')]=False, apply_map: Annotated[bool, typer.Option('--apply', help='Accept the study map on success (requires mvp-0.7).')]=False, create_goal: Annotated[bool, typer.Option('--create-goal', help='Create an exam-prep Goal wired to the minted facets.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1145) — Repair and revalidate a failed synthesis run's preserved candidate — ZERO model calls.
- `maintenance_feed_command(action: Annotated[str, typer.Option('--action', help='list|dismiss|snooze.')]='list', notice_id: Annotated[str | None, typer.Option('--notice', help='Notice id for dismiss/snooze.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1237) — Maintenance feed (§11): deterministic notices with per-type aging policies.
- `exam_readiness_command(subject: Annotated[str | None, typer.Option('--subject', help='Restrict to one subject.')]=None, total_items: Annotated[int | None, typer.Option('--total-items', help='Exam item count for per-family variance sizing.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1265) — Fully calibrated exam-readiness report (§15) — deterministic, no LLM.
- `overconfidence_command(goal_id: Annotated[str, typer.Argument(help='Goal id to inspect.')], json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1304) — F5 overconfidence list (§4.3): Ready-high / Demonstrated-false facets.
- `reentry_summary_command(goal_id: Annotated[str, typer.Argument(help='Goal id to inspect.')], json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1330) — F7 welcome-back diff (§4.4): survival-first re-entry summary.
- `decay_pressure_command(goal_id: Annotated[str | None, typer.Option('--goal', help='Scope to a goal (else whole vault).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1358) — F7 no-goal fallback (§4.5): facets by soonest target crossing.
- `source_outcomes_command(subject: Annotated[str | None, typer.Argument(help='Subject id to analyze (all subjects if omitted).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1386) — Provenance-outcome associations (§11) — report-only, additive suggestions.
- `resolve_conflict_command(conflict_id: Annotated[str, typer.Argument(help='source_conflict id.')], kind: Annotated[str, typer.Option('--kind', help='prefer_for_context|keep_both_scoped|notation_mapping|dismiss.')], resolution_file: Annotated[Path | None, typer.Option('--resolution-file', help='JSON resolution payload.')]=None, rationale: Annotated[str | None, typer.Option('--rationale')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1417) — Resolve an open source conflict (§10.2) — never applies either side.
- `synthesis_eval_command(subject: Annotated[str, typer.Argument(help='Fixture subject id (informational; keyed per prompt version).')], set_id: Annotated[str | None, typer.Option('--set', help='Source set to synthesize + score (live provider run).')]=None, gold: Annotated[Path | None, typer.Option('--gold', help='Gold registry YAML (defaults to the bundled fixture).')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for synthesis.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1445) — Score a synthesized study map against a hand-authored gold registry (§14).
- `build_plan_command(refs: Annotated[list[str], typer.Argument(help='Extraction/revision/artifact ids to plan.')], subject: Annotated[str | None, typer.Option('--subject', help='Target subject id (Create-vs-Update routing).')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the build plan as JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1486) — Deterministic build plan with per-stage token estimates (§8.6.2).
- `repair_extraction_command(revision_id: Annotated[str, typer.Argument(help='Source revision id to repair.')], pages: Annotated[str, typer.Option('--pages', help="Page ranges, e.g. '3-5,8'.")], force_ocr: Annotated[bool, typer.Option('--force-ocr', help='Force OCR on the repaired pages.')]=False, inline_math: Annotated[bool, typer.Option('--inline-math', help='Request inline-math extraction.')]=False, table_processing: Annotated[bool, typer.Option('--table-processing', help='Request table processing.')]=False, use_llm: Annotated[bool, typer.Option('--use-llm', help='Approve the external VLM boost (external egress).')]=False, yes: Annotated[bool, typer.Option('--yes', help='Record CLI consent and run the repair.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the durable batch as JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1528) — Consent-gated page-range extraction repair (§2.5).
- `seed_exam_attempts_command(outcomes: Annotated[Path, typer.Option('--outcomes', help='JSON file with per-question exam outcomes.')], exam_date: Annotated[str | None, typer.Option('--exam-date', help="Exam date (YYYY-MM-DD). Overrides the outcomes file's exam_date.")]=None, subject: Annotated[str | None, typer.Option('--subject', help='Only match exam items in this subject.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Report what would be seeded without writing.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1594) — Seed backdated exam_evidence attempts from a past exam's outcomes.
- `doctor(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, fix_state: Annotated[bool, typer.Option('--fix-state', help='Safely sync derived SQLite state.')]=False, fix: Annotated[bool, typer.Option('--fix', help='Rewrite learnloop.toml settings doctor can fix safely: routes, the active provider and the fallback that still name a Codex profile move to the ChatGPT-plan profile of the same tier (ai:codex_route_pinned). Run with --dry-run first.')]=False, ai: Annotated[bool, typer.Option('--ai', help='Include active AI provider health.')]=False, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to check.')]=None, data_quality: Annotated[bool, typer.Option('--data-quality', help='Report collection coverage from a read-only snapshot transaction.')]=False, fix_content: Annotated[bool, typer.Option('--fix-content', help='Repair vault content doctor can fix safely: remove criterion depends_on entries that name no criterion of the item (criterion:unknown_dependency). A criterion that depends on itself is reported, not changed. Run with --dry-run first.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='With --fix or --fix-content: list the edits, write nothing.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1661)
- `independence_audit_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, apply: Annotated[bool, typer.Option('--apply', help='Withdraw invalid beliefs (default: report only).')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1814) — Re-judge beliefs promoted on "independent surface" (augmentation §8, causal §5.6b).
- `trace_evidence_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1874) — A6 trace-evidence report + A1 guard-1 record (spec_measurement_efficiency §3.A1/§3.A6).
- `contract_reachability_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, all_cells: Annotated[bool, typer.Option('--all', help='List REACHABLE cells too, not just the commissioning queue.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1928) — Contract-cell reachability report (spec_measurement_efficiency §5.8.2).
- `inference_precheck_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2003) — Static cells-converted precheck for B1 dominance and B3 entailment.
- `contract_hit_rate_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, since: Annotated[str | None, typer.Option('--since', help='Only attempts created at/after this ISO-8601 timestamp.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2084) — Contract-cell hit rate of recorded attempts (spec_measurement_efficiency §5.8.2).
- `integration_backfill_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, learning_object: Annotated[list[str] | None, typer.Option('--learning-object', help='Restrict to these LO ids (the pilot seam).')]=None, capability: Annotated[list[str] | None, typer.Option('--capability', help="Restrict to integration components declaring these capabilities (default: coordination, plan item 5.2's stated scope).")]=None, apply_changes: Annotated[bool, typer.Option('--apply', help='Write the edits. Without this, diffs only.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2132) — D3's integration gate applied to persisted blueprints (plan item 5.2).
- `facet_mint_gate_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2231) — D2's mint gate re-run over the facets already registered (plan item 5.4).
- `persona_gate_precision_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, since: Annotated[str | None, typer.Option('--since', help='Only count gate outcomes recorded at/after this ISO timestamp.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2301) — §3.0 gate precision, tracked from day one (plan item 5.3).
- `facet_candidates_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=True) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2342) — Harvest facet candidates and lexical review pairs (knowledge-model §3.3).
- `merge_concepts_command(canonical_id: Annotated[str, typer.Argument(help='Concept id to keep.')], duplicate_id: Annotated[str, typer.Argument(help='Concept id to merge into the canonical concept.')], add_alias: Annotated[bool, typer.Option('--alias/--no-alias', help='Add duplicate id, title, and aliases to the canonical concept.')]=True, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show planned file changes without writing.')]=False, force: Annotated[bool, typer.Option('--force', help='Allow merging concepts with conflicting type/description metadata.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2368)
- `review(limit: Annotated[int | None, typer.Option('--limit', help='Maximum queue length.')]=None, available_minutes: Annotated[int | None, typer.Option('--available-minutes', help='Session length.')]=None, energy: Annotated[str | None, typer.Option('--energy', help='Session energy label.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2411)
- `why(practice_item_id: Annotated[str, typer.Argument(help='Practice item id.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2439)
- `show(identifier: Annotated[str, typer.Argument(help='Entity or SQL id.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, causal: Annotated[bool, typer.Option('--causal', help='Render the P1 causal-episode receipt for an attempt.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2477)
- `proposals(json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2585)
- `misconceptions(all_errors: Annotated[bool, typer.Option('--all-errors', help='Include all active error events, not only misconceptions.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2605) — List active error events, defaulting to misconceptions only.
- `resolve_error(event_id: Annotated[str, typer.Argument(help='Error event SQL id.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2680) — Mark an active error event as resolved.
- `accept(patch_id: Annotated[str, typer.Argument(help='Proposal batch id.')], items: Annotated[str | None, typer.Option('--items', help='Comma-separated proposal item SQL ids.')]=None, all_items: Annotated[bool, typer.Option('--all', help='Accept every pending proposal item in the batch.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2699)
- `reject(patch_id: Annotated[str, typer.Argument(help='Proposal batch id.')], items: Annotated[str | None, typer.Option('--items', help='Comma-separated proposal item SQL ids.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2727)
- `edit_proposal_item_command(patch_id: Annotated[str, typer.Argument(help='Proposal batch id.')], item_id: Annotated[str, typer.Argument(help='Proposal item SQL id.')], file: Annotated[Path, typer.Option('--file', help='YAML or JSON replacement payload.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2749)
- `propose(file: Annotated[Path | None, typer.Option('--file', help='AuthoringProposal JSON/YAML file to import.')]=None, subjects: Annotated[str | None, typer.Option('--subjects', help='Comma-separated subject ids for AI context.')]=None, notes: Annotated[str | None, typer.Option('--notes', help='Comma-separated note ids for AI context.')]=None, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra authoring instructions.')]=None, focus_concepts: Annotated[str | None, typer.Option('--focus-concepts', help='Comma-separated concept ids to concentrate the proposal on.')]=None, focus_facets: Annotated[str | None, typer.Option('--focus-facets', help='Comma-separated evidence facet ids to concentrate the proposal on.')]=None, from_goal: Annotated[str | None, typer.Option('--from-goal', help='Active goal id whose concept anchors seed the focus concepts.')]=None, context_stats: Annotated[bool, typer.Option('--context-stats', help='Print authoring context size without running an AI provider.')]=False, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for authoring.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2773)
- `generate_practice(subjects: Annotated[str | None, typer.Option('--subjects', help='Comma-separated subject ids to scan.')]=None, target_items_per_lo: Annotated[int, typer.Option('--target-items-per-lo', min=1, help='Desired active Practice Item count per completed-probe LO.')]=5, max_new_per_lo: Annotated[int, typer.Option('--max-new-per-lo', min=1, help='Maximum new Practice Items to ask for per LO.')]=3, max_los: Annotated[int | None, typer.Option('--max-los', min=1, help='Maximum completed-probe LOs to target.')]=None, focus_concepts: Annotated[str | None, typer.Option('--focus-concepts', help='Comma-separated concept ids; restrict targets to LOs on these concepts.')]=None, focus_facets: Annotated[str | None, typer.Option('--focus-facets', help='Comma-separated evidence facet ids for new items to target.')]=None, from_goal: Annotated[str | None, typer.Option('--from-goal', help='Active goal id whose concept anchors seed the focus concepts.')]=None, los: Annotated[str | None, typer.Option('--los', help='Comma-separated learning-object ids to target; bypasses the item-count deficit gate but keeps the completed-probe gate.')]=None, mode_mix: Annotated[str | None, typer.Option('--mode-mix', help="Hard per-LO practice-mode counts, e.g. 'teach_back=2,short_answer=3'.")]=None, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra generation instructions.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for practice generation.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show targets without calling Codex.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 2892)
- `populate_goal(goal_id: Annotated[str, typer.Argument(help='Active goal id to populate with Practice Items.')], target_items_per_lo: Annotated[int, typer.Option('--target-items-per-lo', min=1, help='Desired practicable (non-exam-reserved) Practice Item count per scope LO.')]=5, max_new_per_lo: Annotated[int, typer.Option('--max-new-per-lo', min=1, help='Maximum new Practice Items to ask for per LO.')]=3, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra generation instructions.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for practice generation.')]=None, review: Annotated[bool, typer.Option('--review', help='Leave the proposal pending review instead of auto-accepting.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show targets without calling the AI provider.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3030) — Generate Practice Items covering an active goal's scope.
- `generate_diagnostics(learning_object_id: Annotated[str | None, typer.Option('--learning-object-id', help='Limit to one Learning Object id.')]=None, max_needs: Annotated[int, typer.Option('--max-needs', min=1, help='Maximum pending intervention needs to target.')]=3, instructions: Annotated[str | None, typer.Option('--instructions', help='Extra diagnostic-generation instructions.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for diagnostic generation.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show targets without calling Codex.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3167)
- `debug_advance(days: Annotated[int, typer.Argument(help="Number of days to advance the vault's derived learning state.")], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3257) — Debug-only: simulate time passing by aging SQLite learning-state timestamps.
- `rebuild_derived_state_command(learning_objects: Annotated[list[str] | None, typer.Option('--learning-object', help='Learning Object id to rebuild. Can be repeated.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3281) — Replay persisted attempt logs to rebuild derived learning state.
- `rebuild_command(shadow: Annotated[bool, typer.Option('--shadow', help='Replay on a scratch database and report semantic deltas.')]=False, set_values: Annotated[list[str] | None, typer.Option('--set', help='Candidate config override as dotted.path=value. Can be repeated.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3319) — Evaluate a candidate whole-history rebuild without changing live state.
- `recall_calibration(json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, assert_bands: Annotated[bool, typer.Option('--assert', help='Exit non-zero when a severity band fails.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3398) — Developer harness for recall-coverage intervention calibration scenarios.
- `observation_templates(include_all: Annotated[bool, typer.Option('--all', help='Include inactive templates.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3421)
- `register_observation_template_command(file: Annotated[Path, typer.Option('--file', help='Observation template YAML or JSON.')], domain: Annotated[str, typer.Option('--domain', help='Template domain.')], version: Annotated[str, typer.Option('--version', help='Template version.')], title: Annotated[str, typer.Option('--title', help='Template title.')], active: Annotated[bool, typer.Option('--active/--inactive', help='Whether the template is active.')]=True, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3446)
- `record_observation_command(template_id: Annotated[str, typer.Argument(help='Observation template id.')], response_json: Annotated[str | None, typer.Option('--response-json', help='Observation response JSON object.')]=None, response_file: Annotated[Path | None, typer.Option('--response-file', help='Observation response YAML or JSON.')]=None, subject: Annotated[str | None, typer.Option('--subject', help='Related subject id.')]=None, learning_object_id: Annotated[str | None, typer.Option('--learning-object-id', help='Resolved Learning Object binding.')]=None, practice_item_id: Annotated[str | None, typer.Option('--practice-item-id', help='Resolved Practice Item binding.')]=None, session_id: Annotated[str | None, typer.Option('--session-id', help='Related session id.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3483)
- `misconception_candidates(practice_item_id: Annotated[str, typer.Argument(help='Practice item id to attach a misconception to.')], query: Annotated[str | None, typer.Option('--query', help='Fuzzy-match text as the learner types.')]=None, limit: Annotated[int, typer.Option('--limit', min=1, help='Maximum candidates to surface.')]=10, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3532) — Rank error-type candidates for the self-grade misconception picker (spec §12.5).
- `misconception_gate_backfill(force: Annotated[bool, typer.Option('--force', help='Re-run and overwrite existing discrimination rows.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3564) — Backfill sim discrimination rows for keyed (item, misconception) pairs (spec §6).
- `attempt(practice_item_id: Annotated[str, typer.Argument(help='Practice item id.')], answer: Annotated[str | None, typer.Option('--answer', help='Learner answer markdown.')]=None, criterion_points: Annotated[str | None, typer.Option('--criterion-points', help='Comma-separated criterion=points pairs.')]=None, fatal_errors: Annotated[str | None, typer.Option('--fatal-errors', help='Comma-separated fatal rubric error ids.')]=None, confidence: Annotated[int, typer.Option('--confidence', min=1, max=5, help='Self-grade confidence 1..5.')]=3, attempt_type: Annotated[str | None, typer.Option('--attempt-type', help='Attempt type. Defaults to the first recording type allowed by the item.')]=None, hints_used: Annotated[int, typer.Option('--hints-used', min=0, help='Number of hints used.')]=0, error_type: Annotated[str | None, typer.Option('--error-type', help='Optional error taxonomy id or literal.')]=None, session_id: Annotated[str | None, typer.Option('--session-id', help='Related session id.')]=None, available_minutes: Annotated[int | None, typer.Option('--available-minutes', help='Remaining session minutes.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for grading.')]=None, no_diagnose: Annotated[bool, typer.Option('--no-diagnose', help='Blind-graded vaults (mvp-0.10 and later): only queue the diagnosis (run it later with `learnloop diagnose drain`).')]=False, stuck: Annotated[bool, typer.Option('--stuck', help='mvp-0.13: the answer was written after "I\'m stuck" (write what you can, or what\'s confusing you). An empty answer is scored 0 with no grader.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan and estimate the grading calls against the caps: no client, no call, no write.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0, help='Grading calls this command may admit (one per sample).')]=10, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help='Metered routes: physical retries and JSON repairs (Codex physical requests are not bounded).')]=4, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help='Metered routes only; not enforced on the Codex subscription.')]=250000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Metered routes only; Codex cost is estimated_only.')]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='USD per million tokens for a metered grading route whose price is unknown (it fails closed).')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 3635) — Record one practice answer: graded by the grading route, else self-graded.
- `today(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4065)
- `eval_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, section: Annotated[str, typer.Option('--section', help='predictions|coverage|gates|retention|propensity|all')]='all', bins: Annotated[int, typer.Option('--bins', help='Calibration bin count.')]=10, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4072) — Legacy callable for the `learnloop eval` group callback (cli.evaluation).
- `exam_calibration_command(json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4087) — Report exam prediction/outcome calibration (Brier, log loss, reliability bins).
- `probe_coverage_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4109) — Hypothesis-contrast / family coverage report (probe redesign §9.5).
- `probe_instances_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, learning_object_id: Annotated[str | None, typer.Option('--lo', help="Only this Learning Object's pending episode.")]=None, seed: Annotated[int, typer.Option('--seed', help='Deterministic generation seed.')]=0, no_llm: Annotated[bool, typer.Option('--no-llm', help='Skip LLM surfaces; use only parametric templates.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON summary.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4150) — Resolve pending diagnostic episodes through instance generation from admitted family/card bindings (probe redesign §10).
- `diagnostic_augmentation_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full Stage-7 report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4213) — B1-B4 evaluation licenses and C1-C4 live receipt/revert telemetry.
- `persona_realism_command(personas: Annotated[Path, typer.Option('--personas', help="JSON list of persona trace strings, or {'traces': [...]}.")], generator_provider: Annotated[str, typer.Option('--generator-provider', help='Provider name that authored these persona traces.')], generator_model: Annotated[str, typer.Option('--generator-model', help='Model that authored these persona traces.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, separation_threshold: Annotated[float, typer.Option('--threshold', help='Separability score that rejects the corpus.')]=0.7, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4247) — Run B2's blinded text-only persona-vs-real matcher and append its license.
- `diagnostic_eval_command(generator_provider: Annotated[str, typer.Option('--generator-provider', help='Configured provider used only to generate planted traces.')], diagnostician_provider: Annotated[str, typer.Option('--diagnostician-provider', help='Configured provider used only to diagnose blind traces.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, cases_file: Annotated[Path | None, typer.Option('--cases', help='JSON planted-case manifest; defaults to vault discrimination profiles.')]=None, sample_count: Annotated[int, typer.Option('--sample-count', min=1, help='Independent C3 samples per case.')]=3, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4321) — Commission B1-B3 with separate configured model providers.
- `scoreboard_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, replay: Annotated[bool, typer.Option('--replay', help='Compute questions_to_certification / certification_regret via the §5.8.1 prefix replay. Copies the sqlite file per cutoff and mutates only the copy; costs ~1.5-3s per cutoff, bisected.')]=False, replay_budget: Annotated[int, typer.Option('--replay-budget', min=1, help='Maximum prefix-replay evaluations. Exhausting it leaves the two certification metrics unavailable rather than guessed.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4413) — The frozen §3 B5 scoreboard (spec_diagnostic_augmentation_v1 §3 B5, Meas §5.7).
- `probe_audit_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4491) — Probe pilot audit (probe redesign §13, Checkpoint 4): predicted-vs-realized EIG, negative realized information, time calibration, cross-surface replication, downstream outcomes, regrade agreement, evidence-source separation, shadow-policy comparison, and the replay determinism c…
- `graph_identifiability_command(subject: Annotated[str | None, typer.Option('--subject', help='Restrict to one subject id.')]=None, schedule_probes: Annotated[bool, typer.Option('--schedule-probes', help='Persist a discriminating probe / coarsen need per finding (§11.3).')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4541) — Assessment identifiability doctor (knowledge-model §11.3).
- `residual_diagnostics_command(subject: Annotated[str | None, typer.Option('--subject', help='Restrict to one subject id.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4598) — Residual-dependence diagnostics (knowledge-model §8.4).
- `probe_regrade_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, limit: Annotated[int, typer.Option('--limit', min=1, help='Maximum observations to regrade.')]=10, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON summary.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4628) — Re-grade a sample of probe observations and record grader agreement per family and grader version (probe redesign §7.6, Checkpoint 4.4).
- `taxonomy_regrade_check_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, limit: Annotated[int, typer.Option('--limit', min=1, help='Maximum attempts to regrade.')]=20, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4660) — Non-destructive mechanism-taxonomy regrade check (knowledge-model §10.1/§16).
- `causal_selection_readiness_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4699) — WP0 readiness for the formal causal selector (decision-value spec §8 Stage 0).
- `causal_attribution_audit_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4771) — Show P0 attribution fill, abstention, and firewall telemetry.
- `instrument_audit_command(since: Annotated[str | None, typer.Option('--since', help='ISO-8601 lower bound on created_at.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4853) — Read every Meas §3 instrument class's REVERT criterion (plan item 6.4).
- `commission_contrast_pairs_command(subject: Annotated[str | None, typer.Option('--subject', help='Restrict to one subject id.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4947) — Turn identifiability findings into A4 contrast-pair authoring requests.
- `cold_probe_schedule_command(learning_object: Annotated[str | None, typer.Option('--lo', help='Schedule one Learning Object instead of the whole vault.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4995) — Queue the delayed cold probe for each certified LO (measurement §5.7).
- `cold_probe_audit_command(json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5062) — `false_certification_rate` and the coverage of the probe lane (§5.7).
- `commission_causal_probes_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, factor: Annotated[str | None, typer.Option('--factor', help='Commission one factor instead of draining the queue.')]=None, item: Annotated[str | None, typer.Option('--item', help='Force a candidate PracticeItem id as the instrument.')]=None, reviewer_verdict: Annotated[Path | None, typer.Option('--adversarial-review', help='JSON file with the independent manipulation review (contract_consistent, measurement_target_independence, undeclared_differences). Without it the audit lands pending_adversarial_review and nothing is minted.')]=None, reviewer_id: Annotated[str | None, typer.Option('--reviewer-id', help='Reviewer identity for the audit (must differ from the generator).')]=None, limit: Annotated[int, typer.Option('--limit', min=1, help='Maximum factors to commission in one run.')]=4, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5124) — Commission discriminating probe instruments for divergent causal factors.
- `review_causal_probe_command(candidate_id: Annotated[str, typer.Argument(help='Causal probe candidate id.')], to_status: Annotated[str, typer.Option('--to', help='registered | reviewed | active | rejected.')], reviewer: Annotated[str | None, typer.Option('--reviewer', help='Reviewer identity (required to review or reject).')]=None, reason: Annotated[str | None, typer.Option('--reason', help='Audit reason for the transition.')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5236) — Walk a commissioned probe up the register → review → activate ladder.
- `build_causal_taxonomy_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, min_cluster_size: Annotated[int, typer.Option('--min-cluster-size', min=2, help='Minimum observations sharing a repair equivalence and discrimination profile required to mint a mechanism.')]=2, activate: Annotated[bool, typer.Option('--activate/--draft', help='Make this immutable snapshot eligible for new receipts.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON artifact.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5274) — Build the P1 mechanism taxonomy as an explicit maintenance batch.
- `correct_measurement_command(source_practice_item_id: Annotated[str, typer.Argument(help='Attempted PracticeItem whose contract is being corrected.')], corrected_item_path: Annotated[Path, typer.Argument(help='YAML containing corrected PracticeItem fields (include a new id to choose it).')], reason: Annotated[str, typer.Option('--reason', help='Required audit reason for the correction.')], projection_version: Annotated[str, typer.Option('--projection-version', help='Exact projection version authorized to consume this correction.')], reinterpret_history: Annotated[bool, typer.Option('--reinterpret-history/--preserve-history', help='Let the named projection reinterpret old evidence when task invariants match.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the append-only correction receipt.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5353) — Supersede an attempted item without rewriting its historical file.
- `probe_families_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, promote: Annotated[str | None, typer.Option('--promote', help='Promote family:version to trusted (gates must recommend it unless --force).')]=None, retire: Annotated[str | None, typer.Option('--retire', help='Retire family:version.')]=None, revise: Annotated[str | None, typer.Option('--revise', help='Create the next draft version of a family id.')]=None, force: Annotated[bool, typer.Option('--force', help='Apply --promote even when the metric gates do not recommend it.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON overview.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5416) — Family-version lifecycle (probe redesign §9.7, Checkpoint 4.7): metric-gated trusted/revise/retire transitions with a persisted audit trail.
- `probe_gate_command(learning_object_id: Annotated[str, typer.Argument(help='Learning Object whose family/card bindings to gate.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, family: Annotated[str | None, typer.Option('--family', help='Only this family template id.')]=None, trials: Annotated[int, typer.Option('--trials', min=1, max=10, help='Planted trials per hypothesis.')]=3, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON results.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 5505) — Run the §9.6 family admission gate with LLM planted-trial traces for one Learning Object's applicable family/card bindings.

## Internal implementation anchors

- `_ready_provider_for_task(*args, **kwargs)` ([source](../../../../../../src/learnloop/cli/app.py), line 40) — Keep package-level monkeypatches working after the CLI package split.
- `_record_command_model_calls(ctx: typer.Context) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 54)
- `_ad_denial_log_database(root: Path) -> Path` ([source](../../../../../../src/learnloop/cli/app.py), line 517)
- `_mark_ad_denial_log(root: Path) -> Any` ([source](../../../../../../src/learnloop/cli/app.py), line 522) — Mark the AD guard's denial log at the upgrade command's start (its identity and length; ``learnloop.adaptive_difficulty.denial_log.cutover_mark``).
- `_archive_ad_denial_log(root: Path, from_version: str, to_version: str, mark: Any) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 536) — Archive the AD guard's denial log once a successful upgrade has completed (owner decision 2026-10-27; ``learnloop.adaptive_difficulty.denial_log``).
- `_echo_ingest_embedding_plan(plan: dict) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 993)
- `_dense_retrieval_note(root: Path) -> dict | None` ([source](../../../../../../src/learnloop/cli/app.py), line 1743) — The doctor's dense-retrieval status note (tutor delivery fixes): per source, how much of its current extraction has block vectors, and whether dense retrieval is effectively on.
- `_echo_fix_content(fix: dict) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 1761)
- `_model_route_lines(routes: list[dict] | None) -> list[str]` ([source](../../../../../../src/learnloop/cli/app.py), line 1783) — Doctor's model-route facts: one line per route that failed since its last completed call (all routes are in --json), then a count of the rest.
- `_storage_line(storage) -> str` ([source](../../../../../../src/learnloop/cli/app.py), line 1806)
- `_source_first_needs(loaded: Any, repository: Any, learning_object_id: str | None, max_needs: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/app.py), line 3145) — Canonical sources S2b (mvp-0.19): textbook exercises before generation.
- `_grading_route_profile(config, explicit: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/app.py), line 3965) — The grading route's provider from config alone (a dry run builds no client).
- `_attempt_grading_estimate(spend, plan, profile: dict[str, Any] | None, *, spend_register_profile: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/app.py), line 3983) — The grading plan, its estimate on the command's caps, and whether it fits.
- `_attempt_diagnosis_note(loaded, plan, *, inline: bool) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/cli/app.py), line 4026) — The conditional inline diagnosis (blind-graded vaults): its own caps.
- `_echo_attempt_plan(payload: dict[str, Any], json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/app.py), line 4043)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/__main__|learnloop.__main__]] — imports `module`
- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `_AsciiSpinner`, `_client_for_provider`, `_parse_mode_mix`, `_ready_provider_for_task`, `_runtime_for_provider`, `module`
- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `upgrade_to_mvp030`; calls `upgrade_to_mvp030`
- [[Reference/Modules/learnloop/adaptive_difficulty/denial_log|learnloop.adaptive_difficulty.denial_log]] — imports `archive_denial_log`, `cutover_mark`; calls `archive_denial_log`, `cutover_mark`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `collecting`, `command_grant`; calls `collecting`, `command_grant`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `MANUAL_PROVIDER`, `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SUBSCRIPTION_PROFILE_TYPES`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendCaps`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION`, `CLAIM_FIXES_ALGORITHM_VERSION`, `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION`, `DATA_CAPTURE_ALGORITHM_VERSION`, `DELIVERABLE_PLAN_ALGORITHM_VERSION`, `FAILURE_SHARE_ALGORITHM_VERSION`, `FOLLOWUP_SERVE_ALGORITHM_VERSION`, `HELP_FOLD_ATTACH_ALGORITHM_VERSION`, `INTERVAL_FACTOR_ALGORITHM_VERSION`, `LATEST_ALGORITHM_VERSION`, `LESSON_OFFERS_ALGORITHM_VERSION`, `LESSON_OPPORTUNITY_ALGORITHM_VERSION`, `LESSON_SUGGESTIONS_ALGORITHM_VERSION`, `ONE_ASK_ALGORITHM_VERSION`, `PHONE_PROBES_ALGORITHM_VERSION`, `READER_FOLLOWUPS_ALGORITHM_VERSION`, `READING_PATH_PLAN_ALGORITHM_VERSION`, `REPLAY_LEDGER_ALGORITHM_VERSION`, `ROUTER_CALIBRATION_ALGORITHM_VERSION`, `ROUTER_FOLLOWUPS_ALGORITHM_VERSION`, `ROUTER_LEARNED_TAIL_ALGORITHM_VERSION`, `ROUTER_OBJECTIVE_ALGORITHM_VERSION`, `SUPERSEDED_CLAIMS_ALGORITHM_VERSION`, `TEACHER_ALGORITHM_VERSION`, `TEACHER_PROBES_ALGORITHM_VERSION`, `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/app_launch|learnloop.app_launch]] — imports `launch_tui`; calls `launch_tui`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `upgrade_to_attempt_content_state`; calls `upgrade_to_attempt_content_state`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `plan_grading_calls`, `validate_attempt_draft`; calls `plan_grading_calls`, `validate_attempt_draft`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `causal_attribution_audit_report`; calls `causal_attribution_audit_report`
- [[Reference/Modules/learnloop/attempts/grading_admission|learnloop.attempts.grading_admission]] — imports `estimated_prompt_tokens`, `grading_admission`; calls `estimated_prompt_tokens`, `grading_admission`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `create_measurement_correction`; calls `create_measurement_correction`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`, `stuck_prompt_active`; calls `stuck_attempt_type`, `stuck_prompt_active`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `trace_evidence_report`; calls `trace_evidence_report`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `BootstrapError`, `create_vault`; calls `create_vault`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `upgrade_to_claim_fixes`; calls `upgrade_to_claim_fixes`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `field_eval`; calls `field_eval`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `command_receipts`, `current_command_recorder`; calls `command_receipts`, `current_command_recorder`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `upgrade_to_cold_retry_reschedule`; calls `upgrade_to_cold_retry_reschedule`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `contract_cell_hit_rate`; calls `contract_cell_hit_rate`
- [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]] — imports `stem_independence_signal`, `stem_shapes`; calls `stem_independence_signal`, `stem_shapes`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `gate_precision`; calls `gate_precision`
- [[Reference/Modules/learnloop/content/authoring/persona_realism|learnloop.content.authoring.persona_realism]] — imports `match_persona_realism`; calls `match_persona_realism`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `build_build_plan`; calls `build_build_plan`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `DurableIngestJobs`; calls `DurableIngestJobs`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `QuickAddError`, `enqueue_quick_add`, `plan_quick_add`; calls `enqueue_quick_add`, `plan_quick_add`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobSpec`; calls `JobSpec`
- [[Reference/Modules/learnloop/content/proposals/conflict_resolution|learnloop.content.proposals.conflict_resolution]] — imports `ConflictResolutionError`, `resolve_conflict`; calls `resolve_conflict`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `analyze_source_outcomes`; calls `analyze_source_outcomes`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `build_source_outline`, `resolve_extraction_id`; calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `SOURCE_SET_SYNTHESIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `BriefValidationError`, `validate_brief`; calls `validate_brief`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `harvest_facet_candidates`; calls `harvest_facet_candidates`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `review_nominator`; calls `review_nominator`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `MintDisposition`, `judge_facet_mints`; calls `judge_facet_mints`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `annotate_mint_report`; calls `annotate_mint_report`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `append_source`, `plan_append_embedding`; calls `append_source`, `plan_append_embedding`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `build_source_coverage`; calls `build_source_coverage`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `create_study_map`, `derive_candidate_repairs`, `plan_study_map_embedding`, `revalidate_synthesis_candidate`; calls `create_study_map`, `derive_candidate_repairs`, `plan_study_map_embedding`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `run_unit_inventory`; calls `run_unit_inventory`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `SelectionValidationError`, `save_unit_selection`; calls `save_unit_selection`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `default_gold_path`, `evaluate`, `extract_candidate_from_vault`, `load_gold`; calls `default_gold_path`, `evaluate`, `extract_candidate_from_vault`, `load_gold`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `COORDINATION`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`; calls `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/schedule_effects|learnloop.daily_plan.schedule_effects]] — imports `schedule_effects`, `serving_schedule`; calls `schedule_effects`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `upgrade_to_mvp014`; calls `upgrade_to_mvp014`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `upgrade_to_data_capture`; calls `upgrade_to_data_capture`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `upgrade_to_mvp022`; calls `upgrade_to_mvp022`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `upgrade_to_deliverable_plan`; calls `upgrade_to_deliverable_plan`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`, `mint_causal_mechanism_taxonomy`; calls `causal_episode_for_attempt`, `mint_causal_mechanism_taxonomy`
- [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]] — imports `causal_lane_health`; calls `causal_lane_health`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`, `resolve_machine_check`; calls `resolve_machine_check`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `transition_probe_candidate`; calls `transition_probe_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning|learnloop.diagnosis.causal_probe_commissioning]] — imports `COMMISSIONING_POLICY_VERSION`, `commission_probe_instrument`; calls `commission_probe_instrument`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `causal_selection_readiness`; calls `causal_selection_readiness`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `commission_contrast_pairs`, `contrast_pair_order_effect`; calls `commission_contrast_pairs`, `contrast_pair_order_effect`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `commission_planted_diagnostic_evaluation`, `diagnostic_augmentation_report`, `model_family`, `planted_cases_from_manifest`; calls `commission_planted_diagnostic_evaluation`, `diagnostic_augmentation_report`, `model_family`, `planted_cases_from_manifest`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `profile_coverage`, `profile_match_fill_rate`; calls `profile_coverage`, `profile_match_fill_rate`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `error_hunt_outcome_summary`, `proofreading_signal`; calls `error_hunt_outcome_summary`, `proofreading_signal`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `missing_vocabulary_report`; calls `missing_vocabulary_report`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `grading_confusion_report`, `pilot_report`, `run_probe_regrade_checks`; calls `grading_confusion_report`, `pilot_report`, `run_probe_regrade_checks`
- [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]] — imports `family_coverage_report`; calls `family_coverage_report`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `applicable_families`, `generate_instances_for_episode`, `run_llm_family_gate`; calls `applicable_families`, `generate_instances_for_episode`, `run_llm_family_gate`
- [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]] — imports `LifecycleTransitionError`, `apply_family_lifecycle_transition`, `evaluate_family_lifecycle`, `family_lifecycle_overview`, `revise_family_version`; calls `apply_family_lifecycle_transition`, `evaluate_family_lifecycle`, `family_lifecycle_overview`, `revise_family_version`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `upgrade_to_mvp012`; calls `upgrade_to_mvp012`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `DEFAULT_REPLAY_BUDGET`, `scoreboard`; calls `scoreboard`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DIAGNOSE_KIND`, `LIVE_DIAGNOSIS_CAPS`, `NOT_NEEDED`, `diagnosis_status`, `drain`; calls `diagnosis_status`, `drain`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `run_taxonomy_regrade_checks`; calls `run_taxonomy_regrade_checks`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `upgrade_to_mvp027`; calls `upgrade_to_mvp027`
- [[Reference/Modules/learnloop/failure_share_upgrade|learnloop.failure_share_upgrade]] — imports `upgrade_to_failure_share`; calls `upgrade_to_failure_share`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `upgrade_to_followup_serve`; calls `upgrade_to_followup_serve`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `certification_cold_probe_report`, `schedule_certification_cold_probes`; calls `certification_cold_probe_report`, `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `exam_readiness_report`; calls `exam_readiness_report`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `upgrade_to_help_fold_attach`; calls `upgrade_to_help_fold_attach`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `backfill_original`; calls `backfill_original`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `fulfil_need_from_sources`, `pending_causal_decision`, `source_first_active`; calls `fulfil_need_from_sources`, `pending_causal_decision`, `source_first_active`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `upgrade_to_mvp029`; calls `upgrade_to_mvp029`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `upgrade_to_interval_factor`; calls `upgrade_to_interval_factor`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `ReachabilityVerdict`, `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `graph_identifiability_report`; calls `graph_identifiability_report`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `apply_independence_audit`, `audit_independent_surface_promotions`; calls `apply_independence_audit`, `audit_independent_surface_promotions`
- [[Reference/Modules/learnloop/learner/inference_precheck|learnloop.learner.inference_precheck]] — imports `analyze_inference_precheck`; calls `analyze_inference_precheck`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `overconfidence_facets`; calls `overconfidence_facets`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `residual_dependence_report`; calls `residual_dependence_report`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `upgrade_to_mvp016`; calls `upgrade_to_mvp016`
- [[Reference/Modules/learnloop/lesson_offers_upgrade|learnloop.lesson_offers_upgrade]] — imports `upgrade_to_lesson_offers`; calls `upgrade_to_lesson_offers`
- [[Reference/Modules/learnloop/lesson_opportunity_upgrade|learnloop.lesson_opportunity_upgrade]] — imports `upgrade_to_lesson_opportunity`; calls `upgrade_to_lesson_opportunity`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `upgrade_to_lesson_suggestions`; calls `upgrade_to_lesson_suggestions`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `upgrade_to_mvp025`; calls `upgrade_to_mvp025`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `upgrade_to_one_ask`; calls `upgrade_to_one_ask`
- [[Reference/Modules/learnloop/ops/content_fixes|learnloop.ops.content_fixes]] — imports `fix_criterion_dependencies`; calls `fix_criterion_dependencies`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `fix_codex_pins`; calls `fix_codex_pins`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `upgrade_to_mvp010`, `upgrade_to_mvp011`, `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`; calls `upgrade_to_mvp010`, `upgrade_to_mvp011`, `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`
- [[Reference/Modules/learnloop/phone_probes_upgrade|learnloop.phone_probes_upgrade]] — imports `upgrade_to_phone_probes`; calls `upgrade_to_phone_probes`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `servable_open_episodes`; calls `servable_open_episodes`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `upgrade_to_mvp015`; calls `upgrade_to_mvp015`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `upgrade_to_mvp017`; calls `upgrade_to_mvp017`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `upgrade_to_reader_followups`; calls `upgrade_to_reader_followups`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `upgrade_to_reading_path_plan`; calls `upgrade_to_reading_path_plan`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `upgrade_to_mvp026`; calls `upgrade_to_mvp026`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `upgrade_to_replay_ledger`; calls `upgrade_to_replay_ledger`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `upgrade_to_mvp020`; calls `upgrade_to_mvp020`
- [[Reference/Modules/learnloop/router_calibration_upgrade|learnloop.router_calibration_upgrade]] — imports `upgrade_to_router_calibration`; calls `upgrade_to_router_calibration`
- [[Reference/Modules/learnloop/router_followups_upgrade|learnloop.router_followups_upgrade]] — imports `upgrade_to_router_followups`; calls `upgrade_to_router_followups`
- [[Reference/Modules/learnloop/router_learned_tail_upgrade|learnloop.router_learned_tail_upgrade]] — imports `upgrade_to_router_learned_tail`; calls `upgrade_to_router_learned_tail`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `upgrade_to_mvp024`; calls `upgrade_to_mvp024`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `upgrade_to_router_objective`; calls `upgrade_to_router_objective`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `upgrade_to_mvp023`; calls `upgrade_to_mvp023`
- [[Reference/Modules/learnloop/scheduling/decay_pressure|learnloop.scheduling.decay_pressure]] — imports `decay_pressure`; calls `decay_pressure`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `reentry_summary`; calls `reentry_summary`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `apply_eligibility_writes`, `cold_check_serve_decision`; calls `apply_eligibility_writes`, `cold_check_serve_decision`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decision_active`, `log_decision`, `pending_writes`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `coverage_line`, `source_coverage`; calls `coverage_line`, `source_coverage`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `upgrade_to_mvp018`, `upgrade_to_mvp019`; calls `upgrade_to_mvp018`, `upgrade_to_mvp019`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `upgrade_to_mvp013`; calls `upgrade_to_mvp013`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `data_quality_report`; calls `data_quality_report`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `upgrade_to_superseded_claims`; calls `upgrade_to_superseded_claims`
- [[Reference/Modules/learnloop/teacher_probes_upgrade|learnloop.teacher_probes_upgrade]] — imports `upgrade_to_teacher_probes`; calls `upgrade_to_teacher_probes`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `upgrade_to_teacher`; calls `upgrade_to_teacher`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`; calls `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `upgrade_to_mvp021`; calls `upgrade_to_mvp021`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `upgrade_to_workbench_field_signals`; calls `upgrade_to_workbench_field_signals`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `functools`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/__main__|learnloop.__main__]], [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]], [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_ad_backfill_dry_run_plans_and_writes_nothing`
  - `test_ad_data_check_is_read_only_and_reports_the_tables`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
  - `test_report_cli_is_read_only_dry_run_first`
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_spend_capped_and_dry_run_first`
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — direct import
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_refusals_and_rejections_quoting_the_learner_never_reach_the_report`
  - `test_the_text_dry_run_prints_the_estimate`
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_the_dry_run_prints_the_estimate_and_writes_nothing`
  - `test_the_hints_report_shows_maps_failures_routes_and_spend`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp037`
  - `test_landing_ii_an_interrupted_mvp036_activation_then_upgrade_to_mvp037_completes_it`
  - `test_the_next_cli_command_completes_an_interrupted_mvp037_activation`
  - `test_upgrade_to_mvp037_works_from_supported_versions`
- [tests/test_auto_build_spend_report.py](../../../../../../tests/test_auto_build_spend_report.py) — direct import
  - `test_sources_report_shows_it_beside_the_source_services`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp035`
  - `test_upgrade_to_mvp035_works_from_every_supported_version`
- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — direct import
  - `test_summary_listing_banner_dismiss_purge_and_cli`
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — direct import
  - `test_feedback_overlay_and_cli_are_receipt_checked`
- [tests/test_causal_trace_consistency_p2.py](../../../../../../tests/test_causal_trace_consistency_p2.py) — direct import
  - `test_cli_renders_probe_need_and_per_hypothesis_state`
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_cli_schedules_and_reports_the_unavailable_arm`
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
  - `test_declined_signin_exits_nonzero`
  - `test_latency_admits_a_metered_plan_exactly_at_the_shared_cap`
  - `test_latency_dry_run_then_a_timed_run`
  - `test_latency_keeps_every_metered_provider_inside_one_dollar_cap`
  - `test_latency_stops_a_later_metered_provider_once_the_shared_cap_is_spent`
  - `test_signin_json_and_no_browser_prints_the_url_to_stderr`
  - `test_signin_opens_the_browser_saves_and_welcomes_once`
  - `test_status_models_resume_and_signout`
  - `test_unknown_provider_is_refused`
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — direct import
  - `test_cli_attempt_defaults_to_allowed_open_text_attempt_type`
  - `test_cli_attempt_json_and_show_attempt`
  - `test_cli_attempt_passes_available_minutes_to_followup_gate`
  - `test_cli_attempt_uses_codex_http_when_runtime_ready`
  - `test_cli_show_attempt_includes_evidence_and_surprise`
- [tests/test_cli_commands.py](../../../../../../tests/test_cli_commands.py) — direct import
  - `test_core_workflow_commands_succeed`
  - `test_exam_answer_refuses_self_grade_flags`
  - `test_exam_answer_refuses_when_no_ai_grader_is_configured`
  - `test_init_add_subject_add_note`
  - `test_misconceptions_lists_and_resolves_active_error_events`
  - `test_propose_accept_reject`
  - `test_today_help_is_available`
- [tests/test_cli_entrypoint.py](../../../../../../tests/test_cli_entrypoint.py) — direct import
  - `test_console_script_target_imports`
  - `test_entrypoint_lists_every_mvp_command`
- [tests/test_cli_fit.py](../../../../../../tests/test_cli_fit.py) — direct import
  - `test_fit_fsrs_refuses_on_empty_vault`
  - `test_fit_show_and_deactivate_round_trip`
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_accepting_diagnostic_proposal_queues_today_followup`
  - `test_generate_diagnostics_dry_run_targets_pending_intervention_need`
  - `test_generate_diagnostics_reports_no_pending_needs`
  - `test_generate_diagnostics_resolves_diagnostic_need_source_refs`
  - `test_generate_diagnostics_runs_codex_http_and_marks_need_fulfilled`
  - `test_generate_practice_dry_run_focus_concepts_filters_targets`
  - `test_generate_practice_dry_run_targets_completed_probe`
  - `test_generate_practice_from_goal_merges_concept_anchors`
  - `test_generate_practice_reports_no_targets_before_probe_completion`
  - `test_generate_practice_runs_codex_http_and_persists_proposal`
  - `test_populate_goal_dry_run_waives_probe_gate_and_ignores_reserved_supply`
  - `test_populate_goal_generates_and_auto_accepts`
  - `test_populate_goal_rejects_unknown_goal`
  - `test_populate_goal_review_flag_leaves_proposal_pending`
  - `test_populate_goal_stops_when_supply_and_contract_are_complete`
  - `test_populate_goal_uses_a_15_minute_provider_timeout`
  - `test_rejecting_review_required_diagnostic_reopens_need_for_regeneration`
- [tests/test_cli_help_snapshot.py](../../../../../../tests/test_cli_help_snapshot.py) — direct import
  - `test_every_command_prints_its_help`
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — direct import
  - `test_cli_ingest_reports_windows_path_escape_hint`
  - `test_cli_ingest_runs_canonical_endpoint_and_reports_json`
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_doctor_json_contract`
  - `test_misconception_gate_backfill_json_contract`
  - `test_proposals_json_contract`
  - `test_review_why_attempt_show_json_contracts`
- [tests/test_cli_observations.py](../../../../../../tests/test_cli_observations.py) — direct import
  - `test_record_observation_emits_attempt_when_practice_binding_is_resolved`
  - `test_record_observation_rejects_two_response_sources`
  - `test_record_observation_without_practice_binding_lands_pending`
  - `test_register_and_list_observation_templates`
- [tests/test_cli_propose.py](../../../../../../tests/test_cli_propose.py) — direct import
  - `test_cli_propose_context_stats_accepts_goal_focus`
  - `test_cli_propose_context_stats_does_not_require_codex_runtime`
  - `test_cli_propose_from_goal_rejects_unknown_goal`
  - `test_cli_propose_import_persists_and_accept_applies`
  - `test_cli_propose_runs_codex_http_authoring_when_runtime_ready`
  - `test_cli_propose_without_file_reports_codex_unavailable`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp038_and_mvp038_refuses_twice`
  - `test_an_interrupted_mvp037_activation_then_upgrade_to_mvp038_completes_it`
  - `test_the_next_cli_command_completes_an_interrupted_mvp038_activation`
  - `test_upgrade_to_mvp038_works_from_supported_versions`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_merge_concepts_cli_json`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_effective_reports_full_model_and_explicit_overrides`
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_cli_dry_runs_and_refuses_unknown_detectors`
  - `test_cli_embed_dry_run_plans_every_t4_recipe`
- [tests/test_contract_commissioning.py](../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_cli_contract_hit_rate`
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_cli_contract_reachability_json_and_exit_code`
  - `test_cli_contract_reachability_on_vault_without_contracts`
- [tests/test_curriculum_c1_landing.py](../../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_ii_a_bare_upgrade_from_mvp038_activates_mvp039_then_mvp040`
  - `test_ii_an_interrupted_mvp040_activation_is_completed_by_the_next_cli_command`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_a_bare_upgrade_targets_mvp040_and_refuses_twice`
  - `test_an_interrupted_mvp039_activation_then_upgrade_to_mvp040_completes_it`
  - `test_the_next_cli_command_completes_an_interrupted_mvp040_activation`
  - `test_upgrade_to_mvp040_works_from_supported_versions`
- [tests/test_data_capture_report.py](../../../../../../tests/test_data_capture_report.py) — direct import
  - `test_a_bad_vault_is_a_plain_refusal`
  - `test_the_command_is_read_only_and_says_each_section`
- [tests/test_debug_advance.py](../../../../../../tests/test_debug_advance.py) — direct import
  - `test_debug_advance_rejects_non_positive_days`
  - `test_debug_advance_shifts_practice_item_state_timestamps`
- [tests/test_decider_agreement.py](../../../../../../tests/test_decider_agreement.py) — direct import
  - `test_agreement_cli_is_read_only_and_reads_review_runs`
  - `test_agreement_counts_each_ledger_row_once_across_a_review_runs_vault_copy`
- [tests/test_deliverable_rpcs.py](../../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_the_report_cli_prints_aggregates_and_refuses_when_off`
- [tests/test_diagnose_review.py](../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_cli_dry_run_report_review_and_data_check`
  - `test_cli_resume_with_only_the_run_dir_keeps_the_original_settings`
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — direct import
  - `test_cli_queue_adjudicate_scoreboard_round_trip`
  - `test_cli_scoreboard_warns_when_no_abstention_case_exists`
- [tests/test_diagnosis_reports.py](../../../../../../tests/test_diagnosis_reports.py) — direct import
  - `test_an_attempt_scoped_command_reserves_only_its_own_diagnosis`
  - `test_cli_drain_and_retry_plan_and_estimate_before_spending`
  - `test_cli_retry_requeues_a_failed_diagnosis`
  - `test_cli_status_drain_retry_and_reports`
  - `test_ctrl_c_stops_the_drain_before_the_next_paid_job`
  - `test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget`
  - `test_retrieval_never_takes_the_call_a_queued_diagnosis_needs`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_persona_realism_cli_runs_the_blind_matcher`
  - `test_stage7_cli_reports_explicitly_empty_producers`
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_reports_reference_issues_and_json_cli`
- [tests/test_e0_dry_run.py](../../../../../../tests/test_e0_dry_run.py) — direct import
  - `test_a_paid_run_is_refused_without_authorization`
  - `test_the_cli_dry_run_with_an_env_file_never_prints_the_key`
- [tests/test_e0_relabel_round.py](../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_paid_cli_passes_reuse_run_and_authorizes_on_the_cumulative_budget`
- [tests/test_e0_review_round1.py](../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes`
- [tests/test_e0_review_round4.py](../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
- [tests/test_e0_review_round4_followup.py](../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_paid_cli_refuses_when_the_lockdown_is_not_in_force`
- [tests/test_e0_review_round5.py](../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_preflight_only_reports_names_and_checks_with_zero_network_and_no_value`
- [tests/test_e1_harness.py](../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_cli_plans_from_e0_manifests_offline`
- [tests/test_e2e_local.py](../../../../../../tests/test_e2e_local.py) — direct import
  - `test_local_only_learning_loop`
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_cli_dry_run_on_disabled_vault_needs_no_provider`
  - `test_cli_requires_explicit_vault`
- [tests/test_embedding_compare.py](../../../../../../tests/test_embedding_compare.py) — direct import
  - `test_cli_compare_dry_run`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_eval_cli_empty_vault_smoke`
  - `test_eval_cli_rejects_unknown_section`
- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_cli_simulate_quick_writes_a_report`
  - `test_cli_simulate_without_a_fit_needs_the_2020_answers`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_a_required_adequate_family_absent_from_the_report_blocks_certification`
  - `test_cli_multisim_quick_fits_every_family_and_reports_claims`
  - `test_cli_multisim_without_fits_needs_the_2020_answers`
  - `test_reanalysis_never_destroys_the_stored_report`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_cli_simulate_passes_an_explicit_bound_through`
  - `test_the_bound_attribution_needs_the_bound_the_other_report_applied`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f3_final_a_cli_open_changes_nothing_else`
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_the_cli_refuses_an_answer_to_an_item_exposed_mid_exam_before_grading_it`
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_the_synthesize_dry_run_plans_the_ingest_judge`
- [tests/test_facet_reword_confirm.py](../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_the_cli_confirms_a_reword`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_cli_dry_run_reports_cost_without_client_or_data_changes`
  - `test_codex_route_dry_run_shows_an_estimate_without_a_price`
  - `test_two_agreeing_passes_apply_and_one_step_undo`
- [tests/test_field_cli.py](../../../../../../tests/test_field_cli.py) — direct import
  - `test_default_eval_stays_the_legacy_calibration_report`
  - `test_eval_families_runs_the_shared_harness_read_only`
  - `test_eval_writes_both_reports_without_models_or_database_writes`
  - `test_field_data_check_read_only_and_no_credentials`
  - `test_field_data_check_requires_explicit_valid_vault`
  - `test_one_explicit_legacy_fallback_for_every_report`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_upgrade_from_the_predecessor_and_through_the_chain`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
  - `test_the_report_cli_never_shows_verified`
- [tests/test_figures_switch_off.py](../../../../../../tests/test_figures_switch_off.py) — direct import
  - `test_the_report_cli_follows_the_switch`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_on_a_database_before_lesson_suggestions_is_refused`
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_the_calibration_report_on_a_seeded_vault`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_registry_audit_cli_is_clean_and_show_traces`
  - `test_registry_certify_links_coverage_without_promoting`
  - `test_registry_certify_refuses_module_constants`
  - `test_registry_promote_advances_status_via_promotion_evidence`
  - `test_registry_release_check_cli_blocks_on_pending_coverage`
  - `test_registry_sweep_scratch_is_removed`
  - `test_retire_surface_from_cli_preserves_evidence_and_logs_reason`
  - `test_reviews_lists_quarantined_then_adjudicate_clears_and_receipt`
- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
  - `test_the_cli_dry_run`
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_synthesize_dry_run_cli_prints_the_plan_and_resolves_no_provider`
- [tests/test_graph_nomination_report.py](../../../../../../tests/test_graph_nomination_report.py) — direct import
  - `test_cli_dry_run_and_flag_conflict`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_documented_two_route_run_fits_the_default_caps_at_the_policy_budget`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_a_bare_upgrade_targets_mvp042_and_it_refuses_twice`
  - `test_an_earlier_links_interrupted_activation_is_handed_down_the_chain`
  - `test_the_next_cli_command_completes_an_interrupted_mvp042_activation`
  - `test_upgrade_to_mvp042_works_from_supported_versions`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_the_report_cli_reads_the_vault_read_only`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name`
- [tests/test_inference_precheck.py](../../../../../../tests/test_inference_precheck.py) — direct import
  - `test_cli_exposes_stable_machine_and_human_precheck`
- [tests/test_init.py](../../../../../../tests/test_init.py) — direct import
  - `test_cli_init_refuses_populated_non_vault_without_force`
  - `test_cli_invalid_starting_level_leaves_no_partial_vault`
- [tests/test_integration_backfill.py](../../../../../../tests/test_integration_backfill.py) — direct import
  - `test_cli_integration_backfill_diff_then_apply`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest`
- [tests/test_label_roles_cli.py](../../../../../../tests/test_label_roles_cli.py) — direct import
  - `test_a_real_run_with_no_model_reachable_calls_and_writes_nothing`
  - `test_an_unknown_source_is_refused`
  - `test_the_cli_dry_run_calls_and_writes_nothing_and_gives_the_plan_and_the_cap`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp036`
  - `test_upgrade_to_mvp036_works_from_every_supported_version`
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_cli_dry_runs_send_and_write_nothing`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f5_gaps_run_reads_on_a_command_budget`
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_the_commands_dry_run_without_starting_anything`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_upgrade_from_the_predecessor_replays_claimed_los_and_through_the_chain`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f2_an_activation_that_cannot_complete_stops_the_opener`
  - `test_f2_attaches_that_never_write_refuse_while_the_journal_stands`
- [tests/test_mcp_cli.py](../../../../../../tests/test_mcp_cli.py) — direct import
  - `test_activity_reports_chat_calls_and_passages_from_the_ledgers`
  - `test_serve_binds_loopback_only_and_names_the_missing_extra`
  - `test_token_show_makes_a_private_stable_token_and_rotate_replaces_it`
- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_secondary_attach_refuses_a_schema_it_does_not_match`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_successor`
- [tests/test_method_phrasing_report.py](../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_f7_the_dry_run_plans_rewrites_and_their_cost`
  - `test_the_cli_with_the_heuristic_proposes`
- [tests/test_mobile_v3_successor.py](../../../../../../tests/test_mobile_v3_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
  - `test_cli_synthesize_records_receipts_with_usage_and_budgets`
  - `test_tui_grading_records_receipts_with_usage`
- [tests/test_model_route_health.py](../../../../../../tests/test_model_route_health.py) — direct import
  - `test_doctor_reports_routes_in_json_and_text_and_flags_the_dead_one`
- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_upgrade_command_takes_the_split_target`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_existing_vaults_keep_their_version_until_the_owner_upgrades`
  - `test_upgrade_command_reaches_mvp011_explicitly_through_the_chain`
  - `test_upgrade_command_still_reaches_mvp010_explicitly`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_upgrade_command_reaches_the_stuck_target_explicitly`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_upgrade_command_reaches_mvp014_explicitly`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_upgrade_command_reaches_mvp017_explicitly`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_upgrade_command_defaults_to_the_latest`
- [tests/test_mvp09_upgrade.py](../../../../../../tests/test_mvp09_upgrade.py) — direct import
  - `test_upgrade_command_reaches_mvp09_target`
- [tests/test_patch_applier.py](../../../../../../tests/test_patch_applier.py) — direct import
  - `test_accept_cli_all_flag_applies_every_pending_item`
  - `test_accept_cli_applies_and_show_proposal_includes_items`
  - `test_accept_cli_rejects_all_with_items`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_cli_generate_dry_run_is_json_and_read_only`
  - `test_cli_generate_refuses_when_disabled_and_rejects_bad_input`
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — direct import
  - `test_eval_cli_reports_without_judge_are_read_only`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_ignored_opening_episode_commissions_no_instrument_generation`
  - `test_probe_instances_reaches_an_ignored_episode_when_the_lo_is_named`
- [tests/test_placement_report.py](../../../../../../tests/test_placement_report.py) — direct import
  - `test_placement_status_lists_open_assumptions`
  - `test_report3_is_aggregate_only_and_read_only`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_cli_doctor_fix_dry_run_then_fix`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_upgrade_from_the_predecessor_and_through_the_chain`
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_batch_dry_runs_never_migrate_an_older_rollback_database`
  - `test_cli_dossier_dry_run_changes_nothing`
  - `test_cli_eval_dry_run_find_coverage_status_and_tool_spec`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_find_dry_run_plans_embedding_and_rerank_without_clients_or_writes`
- [tests/test_probability_cli.py](../../../../../../tests/test_probability_cli.py) — direct import
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_m1_never_writes_state_sqlite`
  - `test_replay_and_rebuild_make_no_git_model_or_subprocess_calls`
- [tests/test_project_hooks.py](../../../../../../tests/test_project_hooks.py) — direct import
  - `test_cli_sweep_exits_zero_on_failures`
- [tests/test_rbeq_pr2_landing.py](../../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_reader_cues_cli_report.py](../../../../../../tests/test_reader_cues_cli_report.py) — direct import
  - `test_a_real_run_with_no_model_reachable_writes_no_link`
  - `test_an_unknown_source_is_refused`
  - `test_the_dry_run_lists_targets_and_shortlists_and_writes_nothing`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_a_bare_upgrade_targets_the_latest_through_mvp039_and_mvp039_refuses_twice`
  - `test_an_interrupted_mvp038_activation_then_upgrade_to_mvp039_completes_it`
  - `test_the_next_cli_command_completes_an_interrupted_mvp039_activation`
  - `test_upgrade_to_mvp039_works_from_supported_versions`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_cli_prints_json_and_leaves_the_database_untouched`
- [tests/test_reading_hardening_review_fixes.py](../../../../../../tests/test_reading_hardening_review_fixes.py) — direct import
  - `test_f1_the_cli_cancel_commits_with_its_settle_too`
- [tests/test_reading_hardening_verify_fixes.py](../../../../../../tests/test_reading_hardening_verify_fixes.py) — direct import
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
- [tests/test_reading_request_sweep.py](../../../../../../tests/test_reading_request_sweep.py) — direct import
  - `test_c_the_cli_cancel_settles_the_request_too`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_upgrade_from_the_predecessor_rebuilds_to_live_and_through_the_chain`
- [tests/test_recall_calibration.py](../../../../../../tests/test_recall_calibration.py) — direct import
  - `test_recall_calibration_cli_json_and_assert_mode`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_the_cli_takes_the_writer_budget_and_split_prices`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_cli_backlog_and_guard_dry_runs`
  - `test_the_cli_report_and_groups_commands`
  - `test_the_upgrade_command_defaults_to_the_latest`
  - `test_the_upgrade_command_prints_the_advisory_guard_status`
  - `test_the_upgrade_command_takes_the_target`
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_upgrade_command_reaches_the_successor`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_the_cli_proposes_the_override_and_accept_applies_it`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_audit_dry_run_calls_and_writes_nothing`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_cli_prints_a_decisions_trace_and_the_report`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_2_the_objective_report_prints_w_and_its_posterior`
- [tests/test_ro6_successor.py](../../../../../../tests/test_ro6_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default`
- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_the_report_states_the_claim_and_lists_versions_and_w_hats_history`
- [tests/test_rofu_successor.py](../../../../../../tests/test_rofu_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_cli_dry_run_plans_one_grading_call`
- [tests/test_router_card.py](../../../../../../tests/test_router_card.py) — direct import
  - `test_router_card_prints_a_decisions_stored_card`
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_the_router_decisions_feed_the_agreement_report`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_router_log_shows_one_decisions_receipt_in_full`
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_the_backfill_dry_runs_and_then_embeds_what_is_missing`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_certification_the_old_reader_stored_no_longer_delivers_checked`
  - `test_dry_run_needs_recheck`
  - `test_dry_run_writes_nothing_and_the_cli_reports_by_reason_key`
  - `test_the_audit_lists_no_equation_of_a_source_held_out_after_its_check`
  - `test_the_bulk_recheck_replaces_a_certification_the_old_reader_stored`
  - `test_the_cli_rechecks_only_what_is_due_and_lists_each_checked_element`
  - `test_the_report_has_a_source_checks_block_only_while_the_switch_is_on`
- [tests/test_rw7b_codex_review_fixes.py](../../../../../../tests/test_rw7b_codex_review_fixes.py) — direct import
  - `test_f4_the_report_without_the_adapter_and_with_the_guide_off_is_as_before`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_cli_json_carries_denominators_and_the_ordering_rationale`
  - `test_cli_prints_the_board_in_b5_order_with_unavailable_arms_visible`
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_landing_f1_the_cli_command_refuses_with_a_clear_message`
- [tests/test_section_coverage_rpcs.py](../../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_the_cli_dry_run_calls_and_writes_nothing`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_tui_open_serves_a_cold_check_submit_would_prime_as_practice`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest`
- [tests/test_shadow_rebuild.py](../../../../../../tests/test_shadow_rebuild.py) — direct import
  - `test_legacy_rebuild_command_keeps_json_shape_and_writes_one_receipt`
  - `test_shadow_rebuild_cli_json_is_stable_and_leaves_live_hash_unchanged`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_adds_imported_source_name_without_replacing_ref_id`
  - `test_show_missing_id_returns_not_found`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_a_live_batch_needs_a_money_cap`
  - `test_harvest_and_verify_dry_runs_send_and_write_nothing`
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_the_cli_dry_run_names_the_source_first_step`
- [tests/test_source_retrieval_cli.py](../../../../../../tests/test_source_retrieval_cli.py) — direct import
  - `test_deep_search_has_a_dry_run_and_caps`
  - `test_sources_search_and_suggest_lo`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_sources_report_gives_p50_and_p90_per_step_and_counts_truncations`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_the_source_recipe_is_never_in_the_default_backfill`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_cli_compare_registers_the_t6_suites`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_the_sources_report_shows_actual_spend_reserved_vs_settled_and_the_largest_operations`
- [tests/test_source_vector_backfill.py](../../../../../../tests/test_source_vector_backfill.py) — direct import
  - `test_doctor_shows_dense_coverage_per_source`
- [tests/test_sources_outcomes_report.py](../../../../../../tests/test_sources_outcomes_report.py) — direct import
  - `test_the_report_groups_and_labels_associations`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_cli_attempt_stuck_and_dont_know_conversion`
  - `test_cli_refuses_stuck_where_it_is_not_offered`
  - `test_tui_ctrl_d_opens_the_stuck_prompt_and_an_empty_submit_records_it`
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
  - `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_the_t8_alias_and_the_v2_llm_arm_are_one_arm_paid_for_once`
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_doctor_fix_content_cli_dry_run_then_apply`
  - `test_doctor_fix_content_cli_reports_self_dependencies_it_leaves`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_a_truncated_latency_call_is_logged_and_failed`
  - `test_the_gaps_command_budgets_with_the_vaults_policy`
  - `test_the_latency_probe_asks_for_each_profiles_policy_budget`
- [tests/test_te3a_successor.py](../../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name`
- [tests/test_te3b_successor.py](../../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name`
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — direct import
  - `test_generate_practice_los_bypasses_item_count_deficit_gate`
  - `test_generate_practice_los_composes_with_focus_concepts_filter`
  - `test_generate_practice_los_keeps_completed_probe_gate`
  - `test_generate_practice_los_unknown_id_errors`
  - `test_generate_practice_mode_mix_adds_hard_constraint_and_teach_back_guidance`
  - `test_generate_practice_mode_mix_drives_requested_item_counts`
  - `test_generate_practice_mode_mix_other_mode_mismatch_soft_warns`
  - `test_generate_practice_mode_mix_parse_error_exits_with_json_error`
  - `test_generate_practice_mode_mix_teach_back_count_violation_is_hard`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_bare_upgrade_goes_through_mvp041_along_the_chain`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_the_cli_upgrade_reaches_the_tag_by_default`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_review_dry_run_plans_and_prices_the_deciders_link_calls`
- [tests/test_tools_cli.py](../../../../../../tests/test_tools_cli.py) — direct import
- [tests/test_tutor_promotion_service.py](../../../../../../tests/test_tutor_promotion_service.py) — direct import
  - `test_cli_accept_reconciles_the_question_promotion`
  - `test_cli_reject_fails_the_question_promotion_request`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f2_the_dry_run_command`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_cli_calibration_reports_read_only`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_the_misconceptions_cli_lists_by_the_diagnosers_verdict_and_adds_fields`
  - `test_the_misconceptions_cli_on_a_joint_vault_only_gains_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/app.py](../../../../../../src/learnloop/cli/app.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
