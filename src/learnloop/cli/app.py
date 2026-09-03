from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403


_runtime_ready_provider_for_task = _ready_provider_for_task


def _ready_provider_for_task(*args, **kwargs):
    """Keep package-level monkeypatches working after the CLI package split."""

    package = sys.modules.get("learnloop.cli")
    override = getattr(package, "_ready_provider_for_task", None) if package else None
    if override is not None and override is not _ready_provider_for_task:
        return override(*args, **kwargs)
    return _runtime_ready_provider_for_task(*args, **kwargs)


app = typer.Typer(no_args_is_help=True, help="LearnLoop local adaptive learning vault.")

@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Vault directory to create.")] = Path("."),
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Allow scaffolding inside a populated directory that is not already a vault.",
        ),
    ] = False,
    subject: Annotated[
        str | None,
        typer.Option("--subject", help="Optional first subject title to seed."),
    ] = None,
    starting_level: Annotated[
        str | None,
        typer.Option(
            "--starting-level",
            help="Optional learner level: new_to_this, some_exposure, comfortable, or strong_background.",
        ),
    ] = None,
    level_note: Annotated[
        str | None,
        typer.Option("--level-note", help="Optional note accompanying --starting-level."),
    ] = None,
) -> None:
    from learnloop.bootstrap import BootstrapError, create_vault

    try:
        result = create_vault(
            path,
            subject=subject,
            starting_level=starting_level,
            level_note=level_note,
            force=force,
        )
    except BootstrapError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Initialized LearnLoop vault at {result.root}")

@app.command("upgrade")
def upgrade(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    to: Annotated[
        str,
        typer.Option(
            "--to",
            help="Target algorithm version (mvp-0.7, mvp-0.8, or mvp-0.9).",
        ),
    ] = "mvp-0.9",
) -> None:
    """Atomically activate a knowledge-model version for this vault.

    ``--to mvp-0.7`` activates the KM2 canonical model over legacy mvp-0.6 content
    (KM §15); ``--to mvp-0.8`` activates the P0 authority-propagation
    projection over an mvp-0.7 vault; ``--to mvp-0.9`` (default) activates
    cross-channel reveal accounting over an mvp-0.8 vault."""

    from learnloop.ops.vault_upgrade import (
        upgrade_to_mvp07,
        upgrade_to_mvp08,
        upgrade_to_mvp09,
    )

    if to == "mvp-0.7":
        result = upgrade_to_mvp07(_root(vault))
    elif to == "mvp-0.8":
        result = upgrade_to_mvp08(_root(vault))
    elif to == "mvp-0.9":
        result = upgrade_to_mvp09(_root(vault))
    else:
        typer.echo(
            f"Unknown target version {to!r}; expected mvp-0.7, mvp-0.8, or mvp-0.9."
        )
        raise typer.Exit(code=2)
    if result.upgraded:
        typer.echo(f"Upgraded vault: {result.from_version} -> {result.to_version}")
        return
    typer.echo(f"Vault not upgraded (currently {result.from_version}):")
    for problem in result.problems:
        typer.echo(f"  - {problem}")
    raise typer.Exit(code=1)

@app.command("add-subject")
def add_subject(
    subject_id: Annotated[str, typer.Argument(help="Kebab-case subject id.")],
    title: Annotated[str, typer.Argument(help="Display title.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    path = add_subject_to_vault(_root(vault), subject_id, title)
    typer.echo(f"Added subject at {path}")

@app.command("add-note")
def add_note(
    subject_id: Annotated[str, typer.Argument(help="Subject id.")],
    note_id: Annotated[str, typer.Argument(help="Note id, with or without note_ prefix.")],
    title: Annotated[str, typer.Argument(help="Note title.")],
    body: Annotated[str, typer.Option("--body", help="Inline note body.")] = "",
    file: Annotated[Path | None, typer.Option("--file", help="Markdown file to use as note body.")] = None,
    source_type: Annotated[
        str,
        typer.Option(
            "--source-type",
            help="Source type: learner_note, canonical_source, or imported.",
        ),
    ] = "learner_note",
    related_los: Annotated[
        str | None,
        typer.Option("--related-los", help="Comma-separated learning object ids to link this note to."),
    ] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    note_body = file.read_text(encoding="utf-8") if file else body
    try:
        path = add_note_to_vault(
            _root(vault),
            subject_id,
            note_id,
            title,
            note_body,
            source_type=source_type,
            related_los=_split_items(related_los),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--source-type") from exc
    typer.echo(f"Added note at {path}")

@app.command()
def ingest(
    source: Annotated[str, typer.Argument(help="URL or local source file to ingest.")],
    kind: Annotated[
        str,
        typer.Option("--kind", help="Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter."),
    ] = "auto",
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id.")] = None,
    learning_objects: Annotated[
        list[str] | None,
        typer.Option("--learning-object", help="Existing Learning Object anchor. Can be repeated."),
    ] = None,
    goal: Annotated[str | None, typer.Option("--goal", help="Active goal id to link ingested concepts to.")] = None,
    allow_auto_captions: Annotated[
        bool | None,
        typer.Option("--allow-auto-captions", help="Allow generated YouTube captions when human captions are unavailable."),
    ] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra canonical-ingestor instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for ingestion.")] = None,
    pdf_engine: Annotated[
        str | None,
        typer.Option("--pdf-engine", help="PDF extraction engine override: auto, marker, or pypdf (\"native\" is a vault-level [ingest.pdf] choice served by the import pipeline)."),
    ] = None,
    pdf_llm: Annotated[
        bool | None,
        typer.Option("--pdf-llm/--no-pdf-llm", help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf])."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    progress_json: Annotated[bool, typer.Option("--progress-json", hidden=True)] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    result = _run_canonical_ingest_command(
        source,
        kind=kind,
        subject=subject,
        learning_objects=learning_objects,
        goal=goal,
        allow_auto_captions=allow_auto_captions,
        instructions=instructions,
        ai_provider=ai_provider,
        pdf_engine=pdf_engine,
        pdf_use_llm=pdf_llm,
        json_output=json_output,
        progress_json=progress_json,
        vault=vault,
    )
    if json_output:
        typer.echo(_dump({"version": 1, "ingest": result.as_dict()}))
        return
    _echo_ingest_summary(result)

@app.command("ingest-exam")
def ingest_exam(
    source: Annotated[str, typer.Argument(help="URL or local past-exam file to ingest.")],
    kind: Annotated[
        str,
        typer.Option("--kind", help="Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter."),
    ] = "auto",
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id.")] = None,
    goal: Annotated[str | None, typer.Option("--goal", help="Active goal id to link ingested concepts to.")] = None,
    instructions: Annotated[
        str | None,
        typer.Option("--instructions", help="Extra instructions appended to the exam-ingest instructions."),
    ] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for ingestion.")] = None,
    pdf_engine: Annotated[
        str | None,
        typer.Option("--pdf-engine", help="PDF extraction engine override: auto, marker, or pypdf (\"native\" is a vault-level [ingest.pdf] choice served by the import pipeline)."),
    ] = None,
    pdf_llm: Annotated[
        bool | None,
        typer.Option("--pdf-llm/--no-pdf-llm", help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf])."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    progress_json: Annotated[bool, typer.Option("--progress-json", hidden=True)] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Ingest a past practice exam: one tagged practice item per exam question.

    Runs the standard canonical ingest pipeline with exam-specific instructions
    (one practice_item per question, tagged exam_q:<n> + exam_question, each
    with a rubric, evidence facets, and a learning object). After reviewing and
    accepting the proposal, seed your per-question outcomes with
    `learnloop seed-exam-attempts --outcomes <file>`.
    """

    result = _run_canonical_ingest_command(
        source,
        kind=kind,
        subject=subject,
        learning_objects=None,
        goal=goal,
        allow_auto_captions=None,
        instructions=exam_ingest_instructions(instructions),
        ai_provider=ai_provider,
        pdf_engine=pdf_engine,
        pdf_use_llm=pdf_llm,
        json_output=json_output,
        progress_json=progress_json,
        vault=vault,
        purpose="exam_ingest",
        spinner_label="Ingesting past exam",
    )
    if json_output:
        typer.echo(_dump({"version": 1, "ingest": result.as_dict()}))
        return
    _echo_ingest_summary(result)
    typer.echo(
        "Next: review/accept the proposal (learnloop proposals / learnloop accept), "
        "then run: learnloop seed-exam-attempts --outcomes <outcomes.json>"
    )

@app.command("import")
def import_sources(
    sources: Annotated[list[str], typer.Argument(help="URLs, arXiv ids, or local files to import.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Optional subject id for the batch.")] = None,
    inventory: Annotated[bool, typer.Option("--inventory", help="Also queue role-specific unit inventories.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the durable batch as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Import sources into the vault library through the durable queue (§6.1).

    Enqueues one durable ``import`` job per source and drains them in the
    foreground when no sidecar worker holds the lease."""

    from learnloop.content.pipeline.runner import JobSpec

    vault_root = _root(vault)
    _load_vault_or_exit(vault_root, json_output=json_output)
    runner = _ingest_runner(vault_root)
    specs: list[JobSpec] = []
    for source in sources:
        import_index = len(specs)
        specs.append(JobSpec("import", {"source": source}))
        if inventory:
            specs.append(JobSpec("inventory", {"source": source}, depends_on=(import_index,)))
    workflow = "import_inventory" if inventory else "import"
    batch_id = runner.enqueue_batch(workflow, specs, subject_id=subject)
    runner.recover_stale_leases()
    runner.drain()
    payload = _batch_json(runner, batch_id)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": payload}))
        return
    typer.echo(f"Batch {payload['id']} [{payload['status']}]")
    for job in payload["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<16} {job['status']:<12} {detail or ''}")

@app.command("quick-add")
def quick_add_cmd(
    source: Annotated[str, typer.Argument(help="URL or local file to turn into a study map.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id for the study map.")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the single confirmation prompt.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Quick add (§1): paste one source -> auto-selected units, suggested role,
    default brief, ONE confirmation, then a priority build batch to a study map.

    Imports the source first when it has no completed extraction (acquisition is
    deterministic and token-free — not a consent checkpoint), then plans, confirms
    once, and drains the priority [inventory -> synthesis] batch."""

    from learnloop.content.pipeline.quick_add import QuickAddError, enqueue_quick_add, plan_quick_add
    from learnloop.content.pipeline.jobs import DurableIngestJobs

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    if subject is not None and subject not in loaded.subjects:
        message = f"Subject '{subject}' does not exist."
        typer.echo(_dump({"version": 1, "error": "unknown_subject", "message": message}) if json_output else message, err=not json_output)
        raise typer.Exit(code=1)
    repository = _repository(loaded.root)
    jobs = DurableIngestJobs()
    jobs.bind(repository, vault_root, background=False, lease_ttl_seconds=loaded.config.ingest.runner.lease_ttl_seconds)

    def _plan():
        return plan_quick_add(repository, loaded.config, loaded, source, subject_id=subject)

    try:
        try:
            plan = _plan()
        except QuickAddError as exc:
            if exc.code != "quick_add_requires_import":
                raise
            if not json_output:
                typer.echo(f"Importing {source} ...")
            jobs.enqueue_import([source], subject_id=subject)  # background=False drains inline
            plan = _plan()
    except QuickAddError as exc:
        typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc)}) if json_output else f"{exc.code}: {exc}", err=not json_output)
        raise typer.Exit(code=1)

    confirmation = plan.confirmation()
    if not json_output:
        typer.echo(f"Quick add: {confirmation['title']}")
        scope = "whole source" if confirmation["whole_source"] else f"{confirmation['selected_unit_count']} unit(s)"
        typer.echo(f"  role: {confirmation['suggested_role']}{' (ambiguous — flagged)' if confirmation['role_ambiguous'] else ''}")
        typer.echo(f"  scope: {scope}, ~{confirmation['selected_tokens']} tokens")
        typer.echo(f"  estimated input: ~{confirmation['estimated_input_tokens']} tokens")
        if confirmation["requires_external_ai"]:
            stages = ", ".join(sorted({str(c.get('stage')) for c in confirmation['external_ai_consent']}))
            typer.echo(f"  external AI: yes ({stages})")
    if not yes and not json_output:
        typer.confirm("Proceed with import + synthesis?", abort=True)

    try:
        result = enqueue_quick_add(loaded, jobs, plan)  # background=False drains inline
    except QuickAddError as exc:
        typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc)}) if json_output else f"{exc.code}: {exc}", err=not json_output)
        raise typer.Exit(code=1)

    batch = _batch_json(jobs._require_runner(), result["batch_id"])
    if json_output:
        typer.echo(_dump({"version": 1, "quick_add": result, "batch": batch}))
        return
    typer.echo(f"Batch {batch['id']} [{batch['status']}] -> source set {result['source_set_id']}")
    for job in batch["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<20} {job['status']:<12} {detail or ''}")

@app.command("backfill-originals")
def backfill_originals_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Copy revision originals into the managed store (canonical-sources/raw/).

    Pre-store revisions recorded only original_uri; this retains a
    content-addressed copy for every revision whose local file still exists and
    still matches its asset_hash, so live-source viewers survive file moves.
    """

    from learnloop.ingest.originals import backfill_original

    vault_root = _root(vault)
    repository = _repository(vault_root)
    counts: dict[str, int] = {}
    for artifact in repository.all_source_artifacts():
        for revision in repository.source_revisions_for(artifact["id"]):
            status, _ = backfill_original(
                vault_root,
                digest=revision["asset_hash"],
                original_uri=revision.get("original_uri"),
            )
            counts[status] = counts.get(status, 0) + 1
            if status in {"missing", "hash_mismatch"}:
                typer.echo(f"  {revision['id']} ({artifact['id']}): {status} — {revision.get('original_uri')}")
    summary = ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "no revisions"
    typer.echo(f"backfill-originals: {summary}")

@app.command("source-outline")
def source_outline_command(
    ref: Annotated[str, typer.Argument(help="Extraction, revision, or artifact id to outline.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit the outline as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Deterministic outline of a source's extraction — zero agent runs (§3/§5.7)."""

    from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id

    vault_root = _root(vault)
    repository = _repository(vault_root)
    extraction_id = resolve_extraction_id(repository, ref)
    if extraction_id is None:
        typer.echo(f"No extraction resolves for '{ref}'.", err=True)
        raise typer.Exit(code=1)
    outline = build_source_outline(repository, extraction_id)
    if json_output:
        typer.echo(_dump({"version": 1, "outline": outline.model_dump(mode="json")}))
        return
    typer.echo(f"{outline.title}  [{outline.extractor} {outline.extractor_version}]")
    typer.echo(f"  units={outline.unit_count} blocks={outline.block_count} ~{outline.approx_tokens} tokens")
    if outline.difficult_page_count:
        typer.echo(f"  {outline.difficult_page_count} difficult page(s) flagged for repair")
    for unit in outline.units:
        signals = ",".join(f"{k}={v}" for k, v in unit.structural_signals.items() if v)
        flags = f" flags={','.join(unit.health_flags)}" if unit.health_flags else ""
        typer.echo(f"  {unit.ordinal:>2} {unit.unit_id:<8} {unit.label[:40]:<40} ~{unit.approx_tokens:>6}t {signals}{flags}")

@app.command("select-units")
def select_units_command(
    extraction_id: Annotated[str, typer.Argument(help="Extraction id to record a selection for.")],
    units: Annotated[list[str], typer.Option("--unit", help="Selected unit id (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the stored selection as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Persist a per-extraction unit selection (§5.3)."""

    from learnloop.content.synthesis.source_unit_selection import SelectionValidationError, save_unit_selection

    repository = _repository(_root(vault))
    try:
        selection = save_unit_selection(repository, extraction_id, list(units or []))
    except SelectionValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "selection": selection}))
        return
    typer.echo(f"Selected {len(selection['selected_unit_ids'])} unit(s): {', '.join(selection['selected_unit_ids'])}")

@app.command("inventory")
def inventory_command(
    ref: Annotated[str, typer.Argument(help="Revision / extraction / artifact id.")],
    units: Annotated[list[str] | None, typer.Option("--unit", help="Unit id to inventory (repeatable).")] = None,
    role: Annotated[str, typer.Option("--role", help="Confirmed role (§4.2).")] = "reference",
    profile: Annotated[str | None, typer.Option("--profile", help="semantic|practice|assessment|combined.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for inventory.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Run role-aware unit inventories over selected units (§7)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    extraction_id = resolve_extraction_id(repository, ref)
    if extraction_id is None:
        typer.echo(f"No extraction resolves for '{ref}'.", err=True)
        raise typer.Exit(code=1)
    unit_ids = list(units or [])
    if not unit_ids:
        selection = repository.get_unit_selection(extraction_id)
        unit_ids = (selection or {}).get("selected_unit_ids", [])
    if not unit_ids:
        typer.echo("No units to inventory (pass --unit or record a selection first).", err=True)
        raise typer.Exit(code=1)

    _provider, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "canonical_ingest", ai_provider)
    if client is None:
        typer.echo(runtime.message or "AI provider is unavailable.", err=True)
        raise typer.Exit(code=1)

    results = []
    for unit_id in unit_ids:
        result = run_unit_inventory(
            repository,
            extraction_id,
            unit_id,
            role=role,
            profile=profile,
            client=client,
            input_budget_tokens=loaded.config.ingest.budgets.inventory_input_tokens,
        )
        results.append(
            {"unit_id": unit_id, "inventory_id": result.inventory_id, "profile": result.profile, "cache_hit": result.cache_hit}
        )
    if json_output:
        typer.echo(_dump({"version": 1, "extraction_id": extraction_id, "units": results}))
        return
    for row in results:
        marker = "cached" if row["cache_hit"] else "new"
        typer.echo(f"  {row['unit_id']:<12} {row['profile']:<10} {marker}  {row['inventory_id']}")

@app.command("source-coverage")
def source_coverage_command(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Deterministic coverage + readiness preview for a collection (§9.3)."""

    from learnloop.content.synthesis.source_coverage import build_source_coverage

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    source_set = next((s for s in loaded.source_sets if s.id == set_id), None)
    if source_set is None:
        typer.echo(f"Source set '{set_id}' does not exist.", err=True)
        raise typer.Exit(code=1)
    report = build_source_coverage(repository, loaded, source_set)
    if json_output:
        typer.echo(_dump({"version": 1, "coverage": report}))
        return
    typer.echo(f"Coverage for {report['source_set_id']} ({report['subject_id']})")
    typer.echo(f"  ready={report['readiness']['ready']}")
    for flag in report["readiness"]["flags"]:
        typer.echo(f"  ! {flag['code']}: {flag['message']}")

@app.command("synthesize")
def synthesize_command(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    mode: Annotated[str, typer.Option("--mode", help="auto|bootstrap|append.")] = "auto",
    brief_file: Annotated[Path | None, typer.Option("--brief-file", help="JSON synthesis brief (§8.3).")] = None,
    apply_map: Annotated[bool, typer.Option("--apply", help="Accept the study map under the vault lock (requires mvp-0.7).")] = False,
    create_goal: Annotated[bool, typer.Option("--create-goal", help="Create an exam-prep Goal wired to the minted facets.")] = False,
    new_revision: Annotated[list[str] | None, typer.Option("--new-revision", help="Revision id(s) newly added/changed (append mode).")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for synthesis.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Create or UPDATE a study map from a source set (§8 bootstrap / §10 append).

    mode=auto routes to append when the vault already has an applied study map
    (facets present), else bootstrap — adding a member to a set with a study map
    updates it incrementally with a bounded affected-neighborhood pass."""

    from learnloop.content.synthesis.source_append import append_source
    from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    if not any(s.id == set_id for s in loaded.source_sets):
        typer.echo(f"Source set '{set_id}' does not exist.", err=True)
        raise typer.Exit(code=1)
    brief: dict = {}
    if brief_file is not None:
        from learnloop.content.synthesis.brief import BriefValidationError, validate_brief

        try:
            brief = validate_brief(jsonlib.loads(brief_file.read_text(encoding="utf-8")), strict=True)
        except BriefValidationError as exc:
            typer.echo(f"invalid_brief: {exc}", err=True)
            raise typer.Exit(code=1)

    _provider, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "canonical_ingest", ai_provider)
    if client is None:
        typer.echo(runtime.message or "AI provider is unavailable.", err=True)
        raise typer.Exit(code=1)

    resolved_mode = mode
    if mode == "auto":
        resolved_mode = "append" if loaded.evidence_facets else "bootstrap"

    if resolved_mode == "append":
        try:
            append = append_source(vault_root, set_id, client=client, brief=brief,
                                   new_revision_ids=new_revision)
        except StudyMapError as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc),
                                  "diagnostics": exc.diagnostics}))
            else:
                typer.echo(f"{exc.code}: {exc}", err=True)
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "append": append.as_dict()}))
            return
        typer.echo(f"Updated study map for {append.subject_id} ({append.change_kind}) — proposal {append.proposal_id}")
        typer.echo(f"  auto-applied={len(append.auto_applied_item_ids)} review={len(append.review_item_ids)} items={append.item_counts}")
        typer.echo(f"  study-map diff: {append.study_map_diff}")
        return

    try:
        result = create_study_map(
            vault_root, set_id, client=client, brief=brief, mode=resolved_mode,
            apply=apply_map, create_goal=create_goal,
        )
    except StudyMapError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc),
                              "diagnostics": exc.diagnostics, "lockReasons": exc.lock_reasons}))
        else:
            typer.echo(f"{exc.code}: {exc}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(_dump({"version": 1, "studyMap": result.as_dict()}))
        return
    typer.echo(f"Study map for {result.subject_id} ({result.mode}) — proposal {result.proposal_id}")
    typer.echo(f"  reused={result.reused} applied={result.applied} items={result.item_counts}")
    if result.generation_needs:
        typer.echo(f"  identifiability needs: {len(result.generation_needs)}")
    for diag in result.gate_diagnostics:
        if diag["severity"] != "hard_fail":
            typer.echo(f"  ~ {diag['gate']}: {diag['message']}")

@app.command("synthesize-repair")
def synthesize_repair_command(
    run_id: Annotated[str, typer.Argument(help="Failed synthesis run id with a preserved candidate.")],
    ops_file: Annotated[Path | None, typer.Option("--ops-file", help="JSON list of explicit repair ops (drop_dependency / remap_dependency).")] = None,
    no_auto: Annotated[bool, typer.Option("--no-auto", help="Skip auto-derived repairs; apply only --ops-file.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show stored diagnostics and derived ops without revalidating.")] = False,
    apply_map: Annotated[bool, typer.Option("--apply", help="Accept the study map on success (requires mvp-0.7).")] = False,
    create_goal: Annotated[bool, typer.Option("--create-goal", help="Create an exam-prep Goal wired to the minted facets.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Repair and revalidate a failed synthesis run's preserved candidate — ZERO model calls.

    When synthesis fails hard quality gates the expensive merged candidate stays
    staged on its run. This derives mechanically-safe repairs (e.g. dropping
    item-level dependencies on rubric criterion ids), optionally merges explicit
    ops authored by you or a repair agent, and finishes gates + persistence from
    that checkpoint instead of rerunning the model."""

    from learnloop.content.synthesis.source_set_synthesis import (
        StudyMapError,
        derive_candidate_repairs,
        revalidate_synthesis_candidate,
    )

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    explicit_ops: list[dict] = []
    if ops_file is not None:
        explicit_ops = jsonlib.loads(ops_file.read_text(encoding="utf-8"))
        if not isinstance(explicit_ops, list):
            typer.echo("--ops-file must contain a JSON list of repair ops.", err=True)
            raise typer.Exit(code=1)

    if dry_run:
        run = repository.synthesis_run(run_id)
        if run is None:
            typer.echo(f"Synthesis run '{run_id}' does not exist.", err=True)
            raise typer.Exit(code=1)
        candidate = run.get("candidate_output")
        if not candidate:
            typer.echo(f"Synthesis run '{run_id}' preserved no candidate.", err=True)
            raise typer.Exit(code=1)
        derived = [] if no_auto else derive_candidate_repairs(candidate)
        diagnostics = (run.get("coverage_decisions") or {}).get("gate_diagnostics") or []
        if json_output:
            typer.echo(_dump({"version": 1, "runStatus": run.get("status"),
                              "gateDiagnostics": diagnostics,
                              "derivedOps": derived, "explicitOps": explicit_ops}))
            return
        hard = [d for d in diagnostics if d.get("severity") == "hard_fail"]
        typer.echo(f"Run {run_id} ({run.get('status')}): {len(hard)} hard / {len(diagnostics)} total diagnostics")
        for diag in hard:
            typer.echo(f"  ! {diag.get('gate')}: {diag.get('message')}")
        typer.echo(f"Derived repairs: {len(derived)}  Explicit repairs: {len(explicit_ops)}")
        for op in derived + explicit_ops:
            typer.echo(f"  - {op.get('op')} {op.get('item_client_id')} -> {op.get('dep')}"
                       + (f" => {op['to']}" if op.get("to") else "")
                       + (f"  ({op['reason']})" if op.get("reason") else ""))
        unrepaired = len(hard) - len(derived) - len(explicit_ops)
        if unrepaired > 0:
            typer.echo(f"  {unrepaired} hard failure(s) have no derived repair; author ops via --ops-file.")
        return

    try:
        result = revalidate_synthesis_candidate(
            vault_root, run_id,
            apply=apply_map, create_goal=create_goal,
            repair=not no_auto, repair_ops=explicit_ops,
            repository=repository,
        )
    except StudyMapError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc),
                              "diagnostics": exc.diagnostics}))
        else:
            typer.echo(f"{exc.code}: {exc}", err=True)
            for diag in exc.diagnostics:
                if diag.get("severity") == "hard_fail":
                    typer.echo(f"  ! {diag.get('gate')}: {diag.get('message')}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(_dump({"version": 1, "studyMap": result.as_dict()}))
        return
    applied_ops = [op for op in result.candidate_repairs if op.get("applied")]
    typer.echo(f"Repaired and revalidated run {run_id} — proposal {result.proposal_id}")
    typer.echo(f"  repairs applied={len(applied_ops)} applied_map={result.applied} items={result.item_counts}")
    for op in applied_ops:
        typer.echo(f"  - {op.get('op')} {op.get('item_client_id')} -> {op.get('dep')}")

@app.command("maintenance-feed")
def maintenance_feed_command(
    action: Annotated[str, typer.Option("--action", help="list|dismiss|snooze.")] = "list",
    notice_id: Annotated[str | None, typer.Option("--notice", help="Notice id for dismiss/snooze.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Maintenance feed (§11): deterministic notices with per-type aging policies."""

    from learnloop.ops.maintenance_feed import dismiss_notice, generate_maintenance_feed, snooze_notice

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    if action == "dismiss" and notice_id:
        dismiss_notice(repository, notice_id)
    elif action == "snooze" and notice_id:
        snooze_notice(repository, notice_id)
    feed = generate_maintenance_feed(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "notices": feed}))
        return
    if not feed:
        typer.echo("Maintenance feed is clear.")
        return
    for notice in feed:
        typer.echo(f"[{notice['severity']}] {notice['notice_type']}: {notice['title']}  -> {notice['action'].get('action')} ({notice['id']})")

@app.command("exam-readiness")
def exam_readiness_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject.")] = None,
    total_items: Annotated[int | None, typer.Option("--total-items", help="Exam item count for per-family variance sizing.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Fully calibrated exam-readiness report (§15) — deterministic, no LLM.

    Predicted score distribution per task family (mean/variance) against
    practice-exam Brier calibration where data exists; Ready vs Demonstrated
    are reported side by side, never blended."""

    from learnloop.goals.exam_readiness import exam_readiness_report

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    report = exam_readiness_report(loaded, repository, subject_id=subject, total_exam_items=total_items)
    if json_output:
        typer.echo(_dump({"version": 1, "report": report.as_dict()}))
        return
    typer.echo(f"Exam readiness (Ready vs Demonstrated) — {len(report.rows)} task families")
    for row in report.rows:
        ready = f"{row.ready:.2f}" if row.ready is not None else "n/a"
        std = f"±{row.predicted['std']:.2f}" if row.predicted else ""
        typer.echo(
            f"  {row.task_family}: weight={row.normalized_weight:.2f} "
            f"predicted={ready}{std} demonstrated={row.demonstrated_fraction:.2f}"
        )
    if report.predicted_score is not None:
        ps = report.predicted_score
        typer.echo(
            f"Predicted exam score: {ps['mean']:.2f} ± {ps['std']:.2f} (predicted performance) | "
            f"demonstrated {report.demonstrated_score:.2f} (evidence banked)"
        )
    if report.has_calibration:
        typer.echo("Calibration overlay: past practice-exam predictions available (Brier); see --json.")

@app.command("overconfidence")
def overconfidence_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """F5 overconfidence list (§4.3): Ready-high / Demonstrated-false facets."""

    from learnloop.learner.overconfidence import overconfidence_facets

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    goal = _find_goal_or_exit(loaded, goal_id)
    facets = overconfidence_facets(loaded, repository, goal)
    if json_output:
        typer.echo(_dump({"version": 1, "facets": [f.as_dict() for f in facets]}))
        return
    typer.echo(f"Overconfidence list — {len(facets)} facet(s)")
    for facet in facets:
        typer.echo(
            f"  {facet.facet_id} ({facet.learning_object_title}): "
            f"ready={facet.ready:.2f} weight={facet.blueprint_weight:.2f} "
            f"mass={facet.evidence_mass:.2f} score={facet.score:.3f}"
        )

@app.command("reentry-summary")
def reentry_summary_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """F7 welcome-back diff (§4.4): survival-first re-entry summary."""

    from learnloop.scheduling.reentry_summary import reentry_summary

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    goal = _find_goal_or_exit(loaded, goal_id)
    summary = reentry_summary(loaded, repository, goal)
    if json_output:
        typer.echo(_dump({"version": 1, "summary": summary.as_dict()}))
        return
    if not summary.show:
        typer.echo(f"No welcome-back panel (gap {summary.gap_days}d ≤ {summary.threshold_days}d).")
        return
    named = ", ".join(f.facet_id for f in summary.slipped_top) or "none"
    typer.echo(
        f"Welcome back ({summary.gap_days}d away). Still solid: {summary.solid_count}. "
        f"Slipped: {summary.slipped_count} — {named}. "
        f"Best next session: {summary.refresher_count} refreshers."
    )

@app.command("decay-pressure")
def decay_pressure_command(
    goal_id: Annotated[str | None, typer.Option("--goal", help="Scope to a goal (else whole vault).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """F7 no-goal fallback (§4.5): facets by soonest target crossing."""

    from learnloop.scheduling.decay_pressure import decay_pressure

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    goal = _find_goal_or_exit(loaded, goal_id) if goal_id else None
    pressure = decay_pressure(loaded, repository, goal=goal)
    if json_output:
        typer.echo(_dump({"version": 1, "pressure": pressure.as_dict()}))
        return
    typer.echo(
        f"Decay pressure — {len(pressure.facets)} facet(s), "
        f"{pressure.held_flat_count} held flat (not enough history)"
    )
    for facet in pressure.facets:
        when = "now" if facet.crosses_in_days == 0 else (
            f"~{facet.crosses_in_days}d" if facet.crosses_in_days is not None else ">horizon"
        )
        typer.echo(f"  {facet.facet_id} ({facet.learning_object_title}): crosses {when}")

@app.command("source-outcomes")
def source_outcomes_command(
    subject: Annotated[str | None, typer.Argument(help="Subject id to analyze (all subjects if omitted).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Provenance-outcome associations (§11) — report-only, additive suggestions.

    Reports ASSOCIATIONS (repeated failure despite exposed coverage; alternate-
    explanation exposure preceding resolution; concepts needing more examples),
    gated on minimum samples with visible uncertainty (counts). Never a source
    ranking, never a state write."""

    from learnloop.content.sources.source_outcome_analytics import analyze_source_outcomes

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    report = analyze_source_outcomes(loaded, repository, subject_id=subject)
    if json_output:
        typer.echo(_dump({"version": 1, "report": report.as_dict()}))
        return
    typer.echo(
        f"Provenance-outcome associations — {len(report.associations)} "
        f"(min_attempts={report.thresholds['min_attempts']}, "
        f"min_exposures={report.thresholds['min_exposures']})"
    )
    for assoc in report.associations:
        typer.echo(f"  [{assoc.kind}] {assoc.title}: {assoc.uncertainty_note}")
        typer.echo(f"    counts={assoc.counts} -> {assoc.suggestion.get('label')}")

@app.command("resolve-conflict")
def resolve_conflict_command(
    conflict_id: Annotated[str, typer.Argument(help="source_conflict id.")],
    kind: Annotated[str, typer.Option("--kind", help="prefer_for_context|keep_both_scoped|notation_mapping|dismiss.")],
    resolution_file: Annotated[Path | None, typer.Option("--resolution-file", help="JSON resolution payload.")] = None,
    rationale: Annotated[str | None, typer.Option("--rationale")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Resolve an open source conflict (§10.2) — never applies either side."""

    from learnloop.content.proposals.conflict_resolution import ConflictResolutionError, resolve_conflict

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(vault_root)
    payload = jsonlib.loads(resolution_file.read_text(encoding="utf-8")) if resolution_file else {}
    try:
        conflict = resolve_conflict(repository, conflict_id, resolution_kind=kind,
                                    resolution=payload, actor="cli", rationale=rationale)
    except ConflictResolutionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "conflict": conflict}))
        return
    typer.echo(f"Conflict {conflict_id} -> {conflict['status']} ({kind})")

@app.command("synthesis-eval")
def synthesis_eval_command(
    subject: Annotated[str, typer.Argument(help="Fixture subject id (informational; keyed per prompt version).")],
    set_id: Annotated[str | None, typer.Option("--set", help="Source set to synthesize + score (live provider run).")] = None,
    gold: Annotated[Path | None, typer.Option("--gold", help="Gold registry YAML (defaults to the bundled fixture).")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for synthesis.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Score a synthesized study map against a hand-authored gold registry (§14)."""

    from learnloop.content.synthesis.ai_contracts import (
        SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    )
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from learnloop.content.synthesis.synthesis_eval import (
        default_gold_path,
        evaluate,
        extract_candidate_from_vault,
        load_gold,
    )

    gold_path = gold or default_gold_path()
    gold_data = load_gold(gold_path)

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    if set_id is not None:
        _provider, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "canonical_ingest", ai_provider)
        if client is None:
            typer.echo(runtime.message or "AI provider is unavailable.", err=True)
            raise typer.Exit(code=1)
        create_study_map(vault_root, set_id, client=client, brief={}, apply=True)
        loaded = load_vault(vault_root)
    candidate = extract_candidate_from_vault(loaded, prompt_version=SOURCE_SET_SYNTHESIS_PROMPT_VERSION)
    report = evaluate(gold_data, candidate)
    if json_output:
        typer.echo(_dump({"version": 1, "eval": report.as_dict()}))
        return
    typer.echo(report.format_text())

@app.command("build-plan")
def build_plan_command(
    refs: Annotated[list[str], typer.Argument(help="Extraction/revision/artifact ids to plan.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id (Create-vs-Update routing).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the build plan as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Deterministic build plan with per-stage token estimates (§8.6.2)."""

    from learnloop.content.pipeline.build_plan import build_build_plan
    from learnloop.content.sources.source_outline import resolve_extraction_id

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    selections: list[dict[str, Any]] = []
    for ref in refs:
        extraction_id = resolve_extraction_id(repository, ref)
        if extraction_id is None:
            typer.echo(f"No extraction resolves for '{ref}'.", err=True)
            raise typer.Exit(code=1)
        selections.append({"extraction_id": extraction_id, "selected_unit_ids": []})
    plan = build_build_plan(repository, loaded.config, loaded, subject_id=subject, selections=selections)
    if json_output:
        typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        return
    totals = plan.as_dict()["totals"]
    typer.echo(f"Build plan  routing={plan.routing}  provider={plan.provider}")
    typer.echo(
        f"  units={totals['selected_unit_count']} calls={totals['calls']} "
        f"input~{totals['input_tokens']}t output<={totals['max_output_tokens']}t "
        f"cache_savings~{totals['cache_savings_tokens']}t"
    )
    for stage in plan.stages:
        marker = " OVER-CEILING" if stage.exceeds_ceiling else ""
        typer.echo(
            f"  {stage.stage:<12} calls={stage.calls} input~{stage.input_tokens}t "
            f"out<={stage.max_output_tokens}t ceiling={stage.ceiling}{marker}"
        )
    for warning in plan.warnings:
        typer.echo(f"  ! {warning}")

@app.command("repair-extraction")
def repair_extraction_command(
    revision_id: Annotated[str, typer.Argument(help="Source revision id to repair.")],
    pages: Annotated[str, typer.Option("--pages", help="Page ranges, e.g. '3-5,8'.")],
    force_ocr: Annotated[bool, typer.Option("--force-ocr", help="Force OCR on the repaired pages.")] = False,
    inline_math: Annotated[bool, typer.Option("--inline-math", help="Request inline-math extraction.")] = False,
    table_processing: Annotated[bool, typer.Option("--table-processing", help="Request table processing.")] = False,
    use_llm: Annotated[bool, typer.Option("--use-llm", help="Approve the external VLM boost (external egress).")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Record CLI consent and run the repair.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the durable batch as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Consent-gated page-range extraction repair (§2.5). Requires ``--yes``."""

    from learnloop.content.pipeline.runner import JobSpec

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    if not yes:
        typer.echo("Refusing to run repair without --yes (consent is required).", err=True)
        raise typer.Exit(code=1)
    page_list = [segment.strip() for segment in pages.split(",") if segment.strip()]
    provider = loaded.config.ingest.pdf.llm_service if use_llm else "local"
    consent = {
        "provider": provider,
        "purpose": "extraction_repair",
        "pages": page_list,
        "cached": False,
        "consented_via": "cli --yes",
        "external": bool(use_llm),
    }
    repair_options = {
        "force_ocr": force_ocr,
        "inline_math": inline_math,
        "table_processing": table_processing,
        "use_llm": use_llm,
    }
    runner = _ingest_runner(vault_root)
    if runner.repo.get_source_revision(revision_id) is None:
        typer.echo(f"Revision '{revision_id}' was not found.", err=True)
        raise typer.Exit(code=1)
    batch_id = runner.enqueue_batch(
        "extraction_repair",
        [
            JobSpec(
                "extraction_repair",
                {
                    "revision_id": revision_id,
                    "pages": page_list,
                    "repair_options": repair_options,
                    "consent": consent,
                },
            )
        ],
    )
    runner.recover_stale_leases()
    runner.drain()
    payload = _batch_json(runner, batch_id)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": payload}))
        return
    typer.echo(f"Repair batch {payload['id']} [{payload['status']}]")
    for job in payload["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['job_type']:<18} {job['status']:<12} {detail or ''}")

@app.command("seed-exam-attempts")
def seed_exam_attempts_command(
    outcomes: Annotated[Path, typer.Option("--outcomes", help="JSON file with per-question exam outcomes.")],
    exam_date: Annotated[
        str | None,
        typer.Option("--exam-date", help="Exam date (YYYY-MM-DD). Overrides the outcomes file's exam_date."),
    ] = None,
    subject: Annotated[str | None, typer.Option("--subject", help="Only match exam items in this subject.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Report what would be seeded without writing.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Seed backdated exam_evidence attempts from a past exam's outcomes.

    Matches outcomes against practice items tagged exam_q:<n> (created by
    `learnloop ingest-exam`), records one discounted attempt per question dated
    at the exam date, then rebuilds derived state so mastery/FSRS replay in
    time order.
    """

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    try:
        payload = _load_mapping_file(outcomes, label="outcomes file")
        parsed = parse_exam_outcomes(payload, exam_date_override=exam_date)
        result = seed_exam_attempts(
            loaded,
            repository,
            outcomes=parsed,
            subject=subject,
            dry_run=dry_run,
        )
    except (ExamSeedingError, ValueError, OSError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_seeding_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_seeding": result.as_dict()}))
        return
    for entry in result.entries:
        if entry.status in {"seeded", "would_seed"}:
            verb = "Seeded" if entry.status == "seeded" else "Would seed"
            typer.echo(
                f"{verb} q{entry.question} -> {entry.practice_item_id} "
                f"(score={entry.score:.2f}, rubric_score={entry.rubric_score})"
            )
        elif entry.status == "skipped_existing":
            typer.echo(f"Skipped q{entry.question} -> {entry.practice_item_id}: {entry.detail}")
        else:
            typer.echo(f"Warning q{entry.question} -> {entry.practice_item_id}: {entry.detail}")
    summary = (
        f"exam_date={result.exam_date} seeded={result.seeded_count} "
        f"skipped={result.skipped_existing_count} no_outcome={result.no_outcome_count}"
    )
    if dry_run:
        summary = f"[dry-run] {summary}"
    elif result.rebuild is not None:
        summary += (
            f" rebuilt_learning_objects={result.rebuild.rebuilt_learning_objects}"
            f" replayed_attempts={result.rebuild.replayed_attempts}"
        )
    typer.echo(summary)

@app.command()
def doctor(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    fix_state: Annotated[bool, typer.Option("--fix-state", help="Safely sync derived SQLite state.")] = False,
    ai: Annotated[bool, typer.Option("--ai", help="Include active AI provider health.")] = False,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to check.")] = None,
) -> None:
    report = run_doctor(_root(vault), fix_state=fix_state, ai=ai, ai_provider=ai_provider)
    if json_output:
        typer.echo(_dump(report.as_dict()))
        if not report.clean:
            raise typer.Exit(code=1)
        return
    if report.clean:
        typer.echo("No doctor issues found.")
        return
    for issue in report.issues:
        location = f" ({issue.path})" if issue.path else ""
        subject = f" {issue.entity_id}" if issue.entity_id else ""
        typer.echo(f"{issue.severity}: {issue.code}{subject}: {issue.message}{location}")
    raise typer.Exit(code=1)

@app.command("independence-audit")
def independence_audit_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Withdraw invalid beliefs (default: report only)."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Re-judge beliefs promoted on "independent surface" (augmentation §8, causal §5.6b).

    Arm (b) used to count distinct authored `surface_family` strings, which is
    the parallel notion augmentation §8 forbids; it now recomputes groups with
    `surface_group_id`, the one primitive. This re-checks beliefs promoted under
    the old rule. `--apply` withdraws the invalid ones as `retired_misdiagnosed`,
    which A6 narrates to the learner in the words they were shown — but only for
    beliefs a presentation proves they actually saw. Always exits 0.
    """

    from learnloop.learner.independence_audit import (
        apply_independence_audit,
        audit_independent_surface_promotions,
    )

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    report = (
        apply_independence_audit(loaded, repository)
        if apply
        else audit_independent_surface_promotions(loaded, repository)
    )
    if json_output:
        typer.echo(_dump(report.as_dict()))
        return
    summary = report.summary()
    total = sum(summary.values())
    if not total:
        typer.echo(
            "No beliefs promoted on independent-surface recurrence; nothing to re-judge."
        )
        return
    typer.echo(f"{total} belief(s) promoted on independent-surface recurrence:")
    for verdict in ("holds", "collapsed", "unresolvable", "not_arm_b"):
        typer.echo(f"  {verdict:<14}{summary[verdict]:>5}")
    for row in report.rows:
        if row.verdict == "holds":
            continue
        typer.echo(
            f"  {row.verdict:<13} {row.belief_id} groups={row.group_count} "
            f"items={len(row.item_ids)} — {row.detail}"
        )
        typer.echo(f"      {row.statement[:100]}")
    if report.applied:
        typer.echo(
            f"Withdrew {len(report.withdrawn)} belief(s) as {'retired_misdiagnosed'}; "
            f"{len(report.declined)} declined."
        )
    elif any(row.should_withdraw for row in report.rows):
        typer.echo("Re-run with --apply to withdraw them (A6 narrates the correction).")

@app.command("trace-evidence")
def trace_evidence_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """A6 trace-evidence report + A1 guard-1 record (spec_measurement_efficiency §3.A1/§3.A6).

    Two questions, one report. A6's revert criterion: does opportunistic credit
    concentrate on a few facets — i.e. is the grader pattern-matching the
    vocabulary rather than reading the work? And A1 guard 1's typed record: which
    cells are accruing ``unexercised_supporting_mass``, meaning some item claims
    to consume a facet its learners' traces never touch. Always exits 0.
    """

    from learnloop.attempts.trace_evidence import trace_evidence_report

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    report = trace_evidence_report(repository)
    if json_output:
        typer.echo(_dump({"version": 1, **report}))
        return
    typer.echo(
        f"{report['declared_observations']} declared + "
        f"{report['opportunistic_observations']} opportunistic observation(s) "
        f"across {report['attempts_with_observations']} attempt(s)."
    )
    concentration = report["opportunistic_concentration"]
    if concentration is None:
        typer.echo(
            "  concentration: unavailable (fewer than 5 opportunistic observations "
            "— reporting a share here would be noise, not a signal)"
        )
    else:
        typer.echo(
            f"  concentration: {concentration:.0%} of opportunistic observations on one "
            f"facet, across {report['distinct_opportunistic_facets']} distinct facet(s)"
        )
    for row in report["top_opportunistic_facets"]:
        typer.echo(f"    {row['facet_id']:<44}{row['count']:>5}")
    count = report["unexercised_supporting_cell_count"]
    if not count:
        typer.echo("  no unexercised supporting targets recorded.")
        return
    typer.echo(f"  {count} cell(s) with unexercised supporting mass (A1 guard 1):")
    for row in report["unexercised_supporting_cells"]:
        typer.echo(
            f"    {row['facet_id']}@{row['capability']} "
            f"unexercised={row['unexercised_supporting_mass']:.3f} "
            f"direct_credit={row['direct_certification_credit']:.3f} "
            f"embedded_credit={row['embedded_certification_credit']:.3f}"
        )

@app.command("contract-reachability")
def contract_reachability_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    all_cells: Annotated[
        bool,
        typer.Option("--all", help="List REACHABLE cells too, not just the commissioning queue."),
    ] = False,
) -> None:
    """Contract-cell reachability report (spec_measurement_efficiency §5.8.2).

    Pure static analysis: for every ``(learning object, facet, required
    capability)`` cell a blueprint recipe names, can any authored item observe it
    at that capability? ``REACHABLE`` / ``MISMATCH_ABOVE`` / ``MISMATCH_BELOW`` /
    ``NO_INSTRUMENT``. Reads no attempts and no learner state, and doubles as the
    instrument commissioning queue. Always exits 0 — this is a report, not a gate;
    ``learnloop doctor`` carries the same finding as review warnings.
    """

    from learnloop.learner.contract_reachability import (
        ReachabilityVerdict,
        analyze_contract_reachability,
    )

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    report = analyze_contract_reachability(loaded)
    if json_output:
        payload = report.as_dict() if all_cells else {
            "version": 1,
            "summary": report.summary(),
            "cells": [row.as_dict() for row in report.commissioning_queue()],
        }
        typer.echo(_dump(payload))
        return

    summary = report.summary()
    if not report.cells:
        typer.echo(
            f"No contract cells: none of {summary['learning_objects_total']} learning "
            "object(s) declare blueprint recipes, so there is nothing to certify "
            "(not a clean bill)."
        )
        return
    share = summary["reachable_share"]
    typer.echo(
        f"{summary['cell_count']} contract cell(s) across {summary['learning_object_count']} "
        f"learning object(s); {summary['instrument_count']} instrument(s)."
    )
    for verdict in ReachabilityVerdict:
        typer.echo(f"  {str(verdict):<16}{summary['counts'][str(verdict)]:>5}")
    typer.echo(
        f"reachable {summary['reachable_count']}/{summary['cell_count']} "
        f"({share:.0%}); unreachable {summary['unreachable_count']}"
    )
    integration_share = summary["integration_reachable_share"]
    if summary["integration_cell_count"]:
        typer.echo(
            f"integration cells {summary['integration_cell_count']}, reachable "
            f"{summary['integration_counts']['REACHABLE']} ({integration_share:.0%})"
        )
    typer.echo(
        f"facets instrumented {summary['facets_instrumented']}/{summary['facets_declared']}"
    )
    queue = report.commissioning_queue() if not all_cells else report.cells
    if queue:
        typer.echo(f"Commissioning queue ({len(queue)} cell(s)):")
    for row in queue:
        observed = ",".join(row.observed_capabilities) or "-"
        typer.echo(
            f"  {str(row.verdict):<15} {row.cell.learning_object_id} "
            f"facet={row.cell.facet_id} required={row.cell.capability} "
            f"observed=[{observed}] remedy={row.remedy}"
        )

@app.command("inference-precheck")
def inference_precheck_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Static cells-converted precheck for B1 dominance and B3 entailment.

    Prices both Wave 4 inference rules against the current contract-reachability
    baseline without reading attempts or learner state and without applying any
    inferred credit.  Untyped/instructional prerequisite edges fail closed;
    path-specific candidates are reported separately because a static pass
    cannot establish that their path was exercised.
    """

    from learnloop.learner.inference_precheck import analyze_inference_precheck

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    report = analyze_inference_precheck(loaded)
    if json_output:
        typer.echo(_dump(report.as_dict()))
        return

    summary = report.summary()
    baseline = summary["baseline"]
    b1 = summary["capability_dominance"]
    b3 = summary["prerequisite_entailment"]
    combined = summary["combined"]
    if baseline["cell_count"] == 0:
        typer.echo(
            "No contract cells are declared; neither inference rule has a "
            "denominator (not a zero-yield verdict)."
        )
        return

    typer.echo(
        f"Baseline: {baseline['reachable_count']}/{baseline['cell_count']} "
        f"contract cell(s) directly reachable; {baseline['unreachable_count']} gap(s)."
    )
    typer.echo(
        f"B1 capability dominance: {b1['cells_converted']} cell(s) converted "
        f"({b1['substitutable_cells']} non-integration)."
    )
    typer.echo(
        f"B3 prerequisite entailment: {b3['cells_converted']} hard-edge cell(s) "
        f"converted; {b3['conditional_cells']} additional path-specific candidate(s)."
    )
    typer.echo(
        f"Combined, deduplicated: {combined['cells_converted']} guaranteed; "
        f"{combined['maximum_cells_converted']} including exercised paths."
    )
    modality_counts = b3["modality_counts"]
    if modality_counts:
        typer.echo(
            "Prerequisite declarations by modality: "
            + ", ".join(
                f"{modality}={count}"
                for modality, count in sorted(modality_counts.items())
            )
        )
    if report.dominance:
        typer.echo("B1 converted cells:")
        for row in report.dominance:
            typer.echo(
                f"  {row.cell.learning_object_id} "
                f"{row.cell.facet_id}@{row.cell.capability} "
                f"<- {','.join(row.source_capabilities)}"
            )
    if report.entailment:
        typer.echo("B3 converted/candidate cells:")
        for row in report.entailment:
            condition = "path-specific" if row.conditional_only else "hard"
            downstream = sorted(
                {source.downstream_learning_object_id for source in row.sources}
            )
            typer.echo(
                f"  {row.cell.learning_object_id} "
                f"{row.cell.facet_id}@{row.cell.capability} "
                f"<- {','.join(downstream)} ({condition})"
            )

@app.command("contract-hit-rate")
def contract_hit_rate_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only attempts created at/after this ISO-8601 timestamp."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Contract-cell hit rate of recorded attempts (spec_measurement_efficiency §5.8.2).

    Step 0's most actionable number, recomputable: of the attempts on LOs that
    declare a contract, what share landed in a ``(facet, capability)`` cell that
    contract requires? On ``fixtures/linear_algebra`` this reproduces its measured
    28%, with the miss split into the rung loss (right facet, wrong capability —
    the only part rung-correct generation can move) and off-contract attempts.
    ``--since`` scopes it to attempts recorded after a change, which is what plan
    item 5.1's hypothesis is stated over. Always exits 0: a report, not a gate.
    """

    from learnloop.content.authoring.contract_commissioning import contract_cell_hit_rate

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    metric = contract_cell_hit_rate(loaded, repository, since=since)
    if json_output:
        typer.echo(_dump(metric.as_dict()))
        return
    if metric.attempts_scored == 0:
        typer.echo(
            f"No scorable attempts ({metric.attempts_total} total; "
            f"{metric.attempts_without_contract} on learning objects with no contract, "
            f"{metric.attempts_missing_item} on missing items, "
            f"{metric.attempts_unrubricked} unrubricked) - no hit rate, not a clean bill."
        )
        return
    typer.echo(f"{metric.attempts_scored} scorable attempt(s) of {metric.attempts_total}.")
    typer.echo(
        f"  contract-cell hits   {metric.cell_hits:>5}  ({metric.cell_hit_rate:.0%})"
    )
    typer.echo(
        f"  rung loss            {metric.facet_only_hits:>5}  ({metric.rung_loss_share:.0%})"
        "  contract facet, wrong capability"
    )
    typer.echo(f"  off contract         {metric.off_contract:>5}")
    typer.echo(f"  facet hit rate       {metric.facet_hit_rate:>5.0%}")

@app.command("integration-backfill")
def integration_backfill_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    learning_object: Annotated[
        list[str] | None,
        typer.Option("--learning-object", help="Restrict to these LO ids (the pilot seam)."),
    ] = None,
    capability: Annotated[
        list[str] | None,
        typer.Option(
            "--capability",
            help="Restrict to integration components declaring these capabilities "
            "(default: coordination, plan item 5.2's stated scope).",
        ),
    ] = None,
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Write the edits. Without this, diffs only."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """D3's integration gate applied to persisted blueprints (plan item 5.2).

    D3 shipped at ingest; §5.8.3 recorded that it cannot repair the components
    already written, because blueprints are vault content and no rebuild touches
    them. This applies the same criterion retroactively: DROP when no separately
    repairable assembly failure is nameable, LOWER when the assembly is real but
    ``coordination`` is unobservable and a shallower authorable rung is still
    deeper than every part, KEEP otherwise (flagged when it is owed an A1
    whole-task capstone). Diff-only unless ``--apply`` — these are hand-authored
    files and the edit is not regenerable.
    """

    from learnloop.curriculum.integration_backfill import (
        COORDINATION,
        apply_integration_backfill_and_recalibrate,
        plan_integration_backfill,
    )

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    report = plan_integration_backfill(
        loaded,
        learning_object_ids=learning_object or None,
        capabilities=capability or [COORDINATION],
    )
    repository = _repository(loaded.root)
    # Dropping cells shrinks 3.3's coverage denominator, so displayed mastery
    # moves with no new evidence. `--apply` therefore rebuilds the affected LOs
    # and writes ONE recalibration boundary (§5.2 / A6); a dry run writes nothing.
    applied = apply_integration_backfill_and_recalibrate(
        loaded, repository, report.verdicts, dry_run=not apply_changes
    )
    edits = applied.edits
    if json_output:
        typer.echo(
            _dump(
                {
                    **report.as_dict(),
                    "applied": apply_changes,
                    **applied.as_dict(),
                }
            )
        )
        return
    summary = report.summary()
    typer.echo(
        f"{summary['integration_component_count']} integration component(s) across "
        f"{summary['learning_objects']} learning object(s); "
        f"coordination observed by some instrument: {summary['coordination_observed']}."
    )
    for disposition, count in summary["dispositions"].items():
        typer.echo(f"  {disposition:<8}{count:>5}")
    for verdict in report.verdicts:
        target = f" -> {verdict.lowered_capability}" if verdict.lowered_capability else ""
        typer.echo(
            f"  {str(verdict.disposition):<6} {verdict.learning_object_id} "
            f"{verdict.blueprint_id}:{verdict.recipe_id} {verdict.capability}{target} "
            f"reason={verdict.reason}"
        )
    if summary["owed_capstones"]:
        typer.echo(
            "Owed an A1 whole-task capstone (kept, flagged): "
            + ", ".join(summary["owed_capstones"])
        )
    for edit in edits:
        typer.echo(f"--- {edit.path}")
        typer.echo(edit.diff)
    typer.echo(
        f"{len(edits)} file(s) {'written' if apply_changes else 'would change (diff only)'}."
    )
    if applied.rebuild_marker_id:
        typer.echo(
            f"Rebuilt {len(applied.rebuilt_learning_object_ids)} learning object(s) and "
            "wrote ONE recalibration boundary — displayed mastery moves with no new "
            "evidence, and the learner is told so exactly once.\n"
            f"  coverage_denominator_version={applied.coverage_denominator_version}"
        )

@app.command("facet-mint-gate")
def facet_mint_gate_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """D2's mint gate re-run over the facets already registered (plan item 5.4).

    Read-only and writes nothing: it re-asks the mint question of every facet in
    the registry, in id order, as if each were arriving at ingest with the ones
    before it already present. That answers "what would D2 have admitted?" on a
    vault whose facets predate the gate, which is the backlog 3.4's
    ``measurement_rank`` measures the consequence of.

    Judged live at ingest by ``source_set_synthesis``; this command is the same
    pure function pointed at history.
    """

    from learnloop.content.synthesis.facet_mint_gate import MintDisposition, judge_facet_mints

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    payloads = [
        facet.model_dump(mode="json")
        for _fid, facet in sorted(loaded.evidence_facets.items())
    ]
    report = judge_facet_mints(payloads)
    if json_output:
        typer.echo(_dump(report.as_dict()))
        return
    summary = report.summary()
    typer.echo(f"{summary['candidate_count']} registered facet(s) re-judged under D2.")
    for disposition, count in summary["dispositions"].items():
        typer.echo(f"  {disposition:<8}{count:>5}")
    for reason, count in summary["reasons"].items():
        if count:
            typer.echo(f"    {reason:<36}{count:>5}")
    for verdict in report.verdicts:
        if verdict.disposition is MintDisposition.MINT:
            continue
        target = f" -> {verdict.alias_of}" if verdict.alias_of else ""
        typer.echo(
            f"  {str(verdict.disposition):<8}{verdict.candidate_id}{target} "
            f"reason={verdict.reason} neighbours={len(verdict.neighbours)}"
        )

@app.command("persona-gate-precision")
def persona_gate_precision_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only count gate outcomes recorded at/after this ISO timestamp."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """§3.0 gate precision, tracked from day one (plan item 5.3).

    Of the items the planted-persona gate blocked or flagged, how many were
    genuinely bad. The denominator is countable today; the numerator needs a
    BLINDED "genuinely bad" label, which only Aug B2's realism matcher / B1's
    planted side can supply — so this reports ``no_producer`` rather than a proxy
    computed from reviewer decisions, which the gate's own reason string causes.
    """

    from learnloop.content.authoring.persona_gate import gate_precision

    repository = _repository(_root(vault))
    metric = gate_precision(repository, since=since)
    if json_output:
        typer.echo(_dump(metric.as_dict()))
        return
    value = "n/a" if metric.value is None else f"{metric.value:.0%}"
    typer.echo(f"{metric.name}: {value}  [{metric.availability}]")
    typer.echo(f"  {metric.numerator if metric.numerator is not None else '-'} / {metric.denominator} {metric.denominator_label}")
    typer.echo(f"  {metric.note}")
    detail = metric.detail
    typer.echo(f"  items judged        {detail.get('items_judged', 0)}")
    for name, tally in (
        ("decisions", detail.get("decisions") or {}),
        ("gated reasons", detail.get("reasons") or {}),
        ("gated classes", detail.get("instrument_classes") or {}),
        ("reviewer decisions", detail.get("reviewer_decisions") or {}),
    ):
        for key, count in sorted(tally.items()):
            if count:
                typer.echo(f"  {name:<19} {key:<34}{count:>5}")

@app.command("facet-candidates")
def facet_candidates_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = True,
) -> None:
    """Harvest facet candidates and lexical review pairs (knowledge-model §3.3).

    Similarity is review-only and never merges; no similarity artifact is
    persisted as identity.
    """

    from learnloop.content.synthesis.facet_candidates import harvest_facet_candidates

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    result = harvest_facet_candidates(loaded, repository)
    if json_output:
        typer.echo(_dump(result))
        return
    typer.echo(f"{len(result['candidates'])} candidate(s), {len(result['review_pairs'])} review pair(s).")
    for pair in result["review_pairs"]:
        typer.echo(f"  review: {pair['left']} ~ {pair['right']} ({pair['similarity']})")

@app.command("merge-concepts")
def merge_concepts_command(
    canonical_id: Annotated[str, typer.Argument(help="Concept id to keep.")],
    duplicate_id: Annotated[str, typer.Argument(help="Concept id to merge into the canonical concept.")],
    add_alias: Annotated[
        bool,
        typer.Option("--alias/--no-alias", help="Add duplicate id, title, and aliases to the canonical concept."),
    ] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show planned file changes without writing.")] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Allow merging concepts with conflicting type/description metadata."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    try:
        result = merge_concepts(
            _root(vault),
            canonical_id,
            duplicate_id,
            add_alias=add_alias,
            dry_run=dry_run,
            force=force,
        )
    except ConceptMergeError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "concept_merge_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "merge": result.as_dict()}))
        return
    prefix = "Would merge" if dry_run else "Merged"
    typer.echo(f"{prefix} {duplicate_id} into {canonical_id}.")
    if result.changed_files:
        typer.echo("Changed files:")
        for path in result.changed_files:
            typer.echo(f"  {path}")
    if result.change_batch_id:
        typer.echo(f"Change batch: {result.change_batch_id}")

@app.command()
def review(
    limit: Annotated[int | None, typer.Option("--limit", help="Maximum queue length.")] = None,
    available_minutes: Annotated[int | None, typer.Option("--available-minutes", help="Session length.")] = None,
    energy: Annotated[str | None, typer.Option("--energy", help="Session energy label.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    run_startup_maintenance(loaded, repository)
    queue = build_due_queue(
        loaded,
        repository,
        limit=limit,
        session=SchedulerSession(available_minutes=available_minutes, energy=energy),
    )
    if json_output:
        typer.echo(_dump(_json_queue(queue)))
        return
    if not queue:
        typer.echo("No scheduled items.")
        return
    for index, item in enumerate(queue, start=1):
        reasons = "; ".join(item.plain_english)
        typer.echo(f"{index}. {item.practice_item_id} priority={item.priority:.3f} mode={item.selected_mode} - {reasons}")

@app.command()
def why(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    run_startup_maintenance(loaded, repository)
    item = explain_practice_item(loaded, repository, practice_item_id)
    if item is None:
        latest = repository.latest_scheduler_explanation(practice_item_id)
        if latest is None:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "not_found", "practice_item_id": practice_item_id}))
            else:
                typer.echo(f"No scheduler explanation for {practice_item_id}.")
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "source": "latest", "explanation": latest}))
            return
        typer.echo(_dump(latest))
        return
    payload = {
        "version": 1,
        "source": "current",
        "practice_item_id": item.practice_item_id,
        "priority": item.priority,
        "components": item.components,
        "readiness_factor": item.readiness_factor,
        "reasons": item.plain_english,
    }
    if json_output:
        typer.echo(_dump(payload))
    else:
        typer.echo(_dump({key: value for key, value in payload.items() if key != "version"}))

@app.command()
def show(
    identifier: Annotated[str, typer.Argument(help="Entity or SQL id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    causal: Annotated[
        bool,
        typer.Option(
            "--causal",
            help="Render the P1 causal-episode receipt for an attempt.",
        ),
    ] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    payload: object | None = None
    entity_type: str | None = None
    if identifier in loaded.learning_objects:
        entity_type = "learning_object"
        payload = loaded.learning_objects[identifier].model_dump(mode="json")
        payload["content_events"] = repository.content_events_for_entity("learning_object", identifier)
        payload["active_source_events"] = repository.active_source_events_for_entity("learning_object", identifier)
    elif identifier in loaded.practice_items:
        entity_type = "practice_item"
        payload = loaded.practice_items[identifier].model_dump(mode="json")
        payload["content_events"] = repository.content_events_for_entity("practice_item", identifier)
        payload["active_source_events"] = repository.active_source_events_for_entity("practice_item", identifier)
    elif identifier in loaded.concepts:
        entity_type = "concept"
        payload = loaded.concepts[identifier]
    elif identifier in loaded.error_types:
        entity_type = "error_type"
        payload = loaded.error_types[identifier]
    elif identifier in loaded.notes:
        entity_type = "note"
        payload = loaded.notes[identifier]
    elif ":t=" in identifier and identifier.split(":t=", 1)[0] in loaded.notes:
        entity_type = "note"
        payload = loaded.notes[identifier.split(":t=", 1)[0]]
    elif identifier in loaded.subjects:
        entity_type = "subject"
        subject = loaded.subjects[identifier]
        payload = {"metadata": subject.metadata.model_dump(mode="json"), "path": subject.path, "body": subject.body}
    else:
        for edge in loaded.edges:
            if edge.id == identifier:
                entity_type = "concept_edge"
                payload = edge
                break
    if payload is None:
        record = repository.find_record(identifier)
        if record is not None:
            entity_type, payload = record
            if entity_type == "practice_attempt" and isinstance(payload, dict):
                payload = {
                    **payload,
                    "grading_evidence": repository.fetch_grading_evidence(identifier),
                    "surprise": repository.latest_attempt_surprise(identifier),
                }
                if causal:
                    from learnloop.diagnosis.causal_attribution import (
                        causal_episode_for_attempt,
                    )

                    payload["causal_episode"] = causal_episode_for_attempt(
                        repository, identifier
                    )
            elif entity_type == "proposal" and isinstance(payload, dict):
                payload = {
                    **payload,
                    "items": repository.proposal_items(identifier),
                }
    if isinstance(payload, dict):
        provenance = payload.get("provenance")
        if isinstance(provenance, dict) and isinstance(
            provenance.get("source_refs"), list
        ):
            payload = {
                **payload,
                "provenance": {
                    **provenance,
                    "source_refs": [
                        source_ref_display_dto(loaded, repository, source_ref)
                        for source_ref in provenance["source_refs"]
                    ],
                },
            }
    if payload is None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "not_found", "identifier": identifier}))
        else:
            typer.echo(f"No entity found for {identifier}.")
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "type": entity_type, "id": identifier, "record": payload}))
    elif entity_type == "practice_attempt" and isinstance(payload, dict):
        _echo_practice_attempt(identifier, payload, repository)
        if causal:
            from learnloop.diagnosis.causal_attribution import (
                causal_episode_for_attempt,
            )

            _echo_causal_episode(
                causal_episode_for_attempt(repository, identifier)
            )
    else:
        typer.echo(_dump(payload if not isinstance(payload, tuple) else {"type": entity_type, "record": payload}))

@app.command()
def proposals(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    batches = list_proposals(_root(vault))
    if json_output:
        typer.echo(_dump({"version": 1, "proposals": batches}))
        return
    if not batches:
        typer.echo("No proposals.")
        return
    for batch in batches:
        typer.echo(f"{batch['id']} status={batch['status_cache']} purpose={batch['purpose']} summary={batch['summary'] or ''}")
        for item in batch.get("items", []):
            typer.echo(
                f"  - {item['id']} {item['item_type']} {item['operation']} "
                f"decision={item['decision']} validation={item['validation_status']}"
            )

@app.command()
def misconceptions(
    all_errors: Annotated[bool, typer.Option("--all-errors", help="Include all active error events, not only misconceptions.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """List active error events, defaulting to misconceptions only."""

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    events = repository.active_error_events()
    if not all_errors:
        events = [event for event in events if event.is_misconception]
    rows = [
        {
            "id": event.id,
            "error_type": event.error_type,
            "title": (error_type.title if (error_type := loaded.error_types.get(event.error_type)) else None),
            "is_misconception": event.is_misconception,
            "severity": event.severity,
            "learning_object_id": event.learning_object_id,
            "created_at": event.created_at,
        }
        for event in events
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "misconceptions": rows}))
        return
    if not rows:
        typer.echo("No active misconceptions." if not all_errors else "No active error events.")
        return
    for row in rows:
        kind = "misconception" if row["is_misconception"] else "error"
        typer.echo(
            f"{row['id']} {row['error_type']} ({kind}) severity={row['severity']:.2f} "
            f"lo={row['learning_object_id']} created={row['created_at']}"
        )
        if row["title"]:
            typer.echo(f"  - {row['title']}")

@app.command("resolve-error")
def resolve_error(
    event_id: Annotated[str, typer.Argument(help="Error event SQL id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Mark an active error event as resolved."""

    repository = _repository(_root(vault))
    resolved = repository.resolve_error_event(event_id)
    if json_output:
        typer.echo(_dump({"version": 1, "event_id": event_id, "resolved": resolved}))
    elif resolved:
        typer.echo(f"Resolved error event {event_id}.")
    else:
        typer.echo(f"Error event {event_id} not found or already resolved.", err=True)
    if not resolved:
        raise typer.Exit(code=1)

@app.command()
def accept(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    items: Annotated[str | None, typer.Option("--items", help="Comma-separated proposal item SQL ids.")] = None,
    all_items: Annotated[bool, typer.Option("--all", help="Accept every pending proposal item in the batch.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    if all_items and items:
        typer.echo("--all cannot be combined with --items.", err=True)
        raise typer.Exit(code=1)
    from learnloop.tutor.promotions import (
        reconcile_accepted_question_promotion_patch,
    )

    vault_root = _root(vault)
    repository = _repository(vault_root)
    try:
        result = accept_items(vault_root, patch_id, _split_items(items))
        # Parity with the sidecar's accept_proposal_items: a tutor question that
        # was promoted into this patch owns a promotion request, and accepting
        # the patch is what completes it. Without this the CLI leaves the request
        # stranded mid-flight while the item is live in the vault.
        reconcile_accepted_question_promotion_patch(repository, patch_id)
    except PatchApplicationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Accepted and applied {result.applied_count} proposal item(s).")

@app.command()
def reject(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    items: Annotated[str | None, typer.Option("--items", help="Comma-separated proposal item SQL ids.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    from learnloop.tutor.promotions import (
        reconcile_rejected_question_promotion_patch,
    )

    vault_root = _root(vault)
    repository = _repository(vault_root)
    try:
        count = reject_items(vault_root, patch_id, _split_items(items))
        # Same parity: a fully rejected promotion patch must surface on the
        # request as a failure the learner can act on, not stay pending forever.
        reconcile_rejected_question_promotion_patch(repository, patch_id)
    except PatchApplicationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Rejected {count} proposal item(s).")

@app.command("edit-proposal-item")
def edit_proposal_item_command(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    item_id: Annotated[str, typer.Argument(help="Proposal item SQL id.")],
    file: Annotated[Path, typer.Option("--file", help="YAML or JSON replacement payload.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    try:
        payload = read_yaml(file) if file.suffix.lower() in {".yaml", ".yml"} else jsonlib.loads(file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Edited payload must be a mapping/object")
        item = edit_proposal_item(_root(vault), patch_id, item_id, payload)
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_edit", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_item": item}))
    else:
        typer.echo(f"Edited proposal item {item_id} validation_status={item['validation_status']}.")

@app.command()
def propose(
    file: Annotated[Path | None, typer.Option("--file", help="AuthoringProposal JSON/YAML file to import.")] = None,
    subjects: Annotated[str | None, typer.Option("--subjects", help="Comma-separated subject ids for AI context.")] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Comma-separated note ids for AI context.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra authoring instructions.")] = None,
    focus_concepts: Annotated[str | None, typer.Option("--focus-concepts", help="Comma-separated concept ids to concentrate the proposal on.")] = None,
    focus_facets: Annotated[str | None, typer.Option("--focus-facets", help="Comma-separated evidence facet ids to concentrate the proposal on.")] = None,
    from_goal: Annotated[str | None, typer.Option("--from-goal", help="Active goal id whose concept anchors seed the focus concepts.")] = None,
    context_stats: Annotated[bool, typer.Option("--context-stats", help="Print authoring context size without running an AI provider.")] = False,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for authoring.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    if context_stats:
        if file is not None:
            message = "--context-stats cannot be combined with --file."
            if json_output:
                typer.echo(_dump({"version": 1, "error": "invalid_request", "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        loaded = load_vault(vault_root)
        resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
            loaded,
            focus_concepts=focus_concepts,
            focus_facets=focus_facets,
            from_goal=from_goal,
            json_output=json_output,
        )
        context = build_authoring_context(
            loaded,
            subjects=_split_items(subjects),
            note_ids=_split_items(notes),
            instructions=instructions,
            focus_concepts=resolved_focus_concepts,
            focus_facets=resolved_focus_facets,
        )
        stats = authoring_context_stats(context)
        if json_output:
            typer.echo(_dump({"version": 1, "authoring_context": stats}))
            return
        counts = stats["counts"]
        chars = stats["chars"]
        sections = chars["sections"]
        typer.echo(
            "Authoring context: "
            f"{counts['subjects']} subject(s), {counts['notes']} note(s), "
            f"{counts['concepts']} concept(s), {counts['learning_objects']} LO(s), "
            f"{counts['practice_items']} PI(s), {counts['goals']} goal(s)."
        )
        typer.echo(
            f"Prompt+schema: {chars['prompt_plus_schema']} chars "
            f"(~{stats['approx_tokens']['prompt_plus_schema']} tokens by chars/4)."
        )
        typer.echo(
            "Sections: "
            f"notes={sections['notes']} chars, concepts={sections['concepts']}, "
            f"learning_objects={sections['learning_objects']}, practice_items={sections['practice_items']}."
        )
        return
    if file is None:
        loaded = load_vault(vault_root)
        resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
            loaded,
            focus_concepts=focus_concepts,
            focus_facets=focus_facets,
            from_goal=from_goal,
            json_output=json_output,
        )
        provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
        if not runtime.ready:
            runtime_status = _runtime_status_for_cli(provider_name, runtime.status)
            runtime_label = "Codex runtime" if provider_name in CODEX_PROVIDER_NAMES else "AI provider"
            message = runtime.message or f"{runtime_label} is {runtime_status}."
            if json_output:
                typer.echo(_dump({"version": 1, "error": runtime_status, "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        try:
            patch_id = generate_authoring_proposal(
                vault_root,
                client,
                subjects=_split_items(subjects),
                note_ids=_split_items(notes),
                instructions=instructions,
                focus_concepts=resolved_focus_concepts,
                focus_facets=resolved_focus_facets,
                model=getattr(client, "model", None),
                codex_revision=getattr(runtime, "actual_revision", None),
            )
        except Exception as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name in CODEX_PROVIDER_NAMES else "ai_failed", "message": str(exc)}))
            else:
                typer.echo(str(exc), err=True)
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "proposal_id": patch_id}))
        else:
            typer.echo(f"Persisted proposal {patch_id}.")
        return
    try:
        raw = read_yaml(file) if file.suffix.lower() in {".yaml", ".yml"} else jsonlib.loads(file.read_text(encoding="utf-8"))
        proposal = AuthoringProposal.model_validate(raw)
        patch_id = persist_authoring_proposal(vault_root, proposal, provider="import")
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_proposal", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_id": patch_id}))
    else:
        typer.echo(f"Persisted proposal {patch_id}.")

@app.command("generate-practice")
def generate_practice(
    subjects: Annotated[str | None, typer.Option("--subjects", help="Comma-separated subject ids to scan.")] = None,
    target_items_per_lo: Annotated[int, typer.Option("--target-items-per-lo", min=1, help="Desired active Practice Item count per completed-probe LO.")] = 5,
    max_new_per_lo: Annotated[int, typer.Option("--max-new-per-lo", min=1, help="Maximum new Practice Items to ask for per LO.")] = 3,
    max_los: Annotated[int | None, typer.Option("--max-los", min=1, help="Maximum completed-probe LOs to target.")] = None,
    focus_concepts: Annotated[str | None, typer.Option("--focus-concepts", help="Comma-separated concept ids; restrict targets to LOs on these concepts.")] = None,
    focus_facets: Annotated[str | None, typer.Option("--focus-facets", help="Comma-separated evidence facet ids for new items to target.")] = None,
    from_goal: Annotated[str | None, typer.Option("--from-goal", help="Active goal id whose concept anchors seed the focus concepts.")] = None,
    los: Annotated[str | None, typer.Option("--los", help="Comma-separated learning-object ids to target; bypasses the item-count deficit gate but keeps the completed-probe gate.")] = None,
    mode_mix: Annotated[str | None, typer.Option("--mode-mix", help="Hard per-LO practice-mode counts, e.g. 'teach_back=2,short_answer=3'.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for practice generation.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling Codex.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    subject_ids = _split_items(subjects)
    try:
        parsed_mode_mix = _parse_mode_mix(mode_mix)
    except ValueError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_mode_mix", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    learning_object_ids = _split_items(los)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
        loaded,
        focus_concepts=focus_concepts,
        focus_facets=focus_facets,
        from_goal=from_goal,
        json_output=json_output,
    )
    try:
        plan = build_practice_expansion_plan(
            loaded,
            repository,
            subjects=subject_ids,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            max_los=max_los,
            focus_concepts=resolved_focus_concepts,
            learning_object_ids=learning_object_ids,
            mode_mix=parsed_mode_mix,
        )
    except PracticeExpansionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_generation_request", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        else:
            _echo_practice_generation_plan(plan)
        return
    if not plan.targets:
        message = "No completed probe Learning Objects need more Practice Items."
        if json_output:
            typer.echo(_dump({"version": 1, "error": "no_targets", "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message)
        raise typer.Exit(code=1)
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
    if not runtime.ready:
        runtime_status = _runtime_status_for_cli(provider_name, runtime.status)
        runtime_label = "Codex runtime" if provider_name in CODEX_PROVIDER_NAMES else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime_status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime_status, "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = generate_post_probe_practice_proposal(
            vault_root,
            client,
            subjects=subject_ids,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            max_los=max_los,
            focus_concepts=resolved_focus_concepts,
            focus_facets=resolved_focus_facets,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
            learning_object_ids=learning_object_ids,
            mode_mix=parsed_mode_mix,
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name in CODEX_PROVIDER_NAMES else "ai_failed", "message": str(exc), "plan": plan.as_dict()}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if result.mode_mix_violations:
        if json_output:
            typer.echo(
                _dump(
                    {
                        "version": 1,
                        "error": "mode_mix_violation",
                        "proposal_id": result.patch_id,
                        "mode_mix_violations": result.mode_mix_violations,
                        "mode_mix_warnings": result.mode_mix_warnings,
                        "plan": result.plan.as_dict(),
                    }
                )
            )
        else:
            typer.echo(f"Persisted practice-generation proposal {result.patch_id}, but the mode mix was not honored:", err=True)
            for violation in result.mode_mix_violations:
                typer.secho(f"- {violation}", fg=typer.colors.RED, err=True)
            for warning in result.mode_mix_warnings:
                typer.secho(f"- warning: {warning}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "proposal_id": result.patch_id,
                    "plan": result.plan.as_dict(),
                    "mode_mix_warnings": result.mode_mix_warnings,
                }
            )
        )
    else:
        typer.echo(f"Persisted practice-generation proposal {result.patch_id}.")
        for warning in result.mode_mix_warnings:
            typer.secho(f"Mode-mix warning: {warning}", fg=typer.colors.YELLOW, err=True)
        _echo_practice_generation_plan(result.plan)

@app.command("populate-goal")
def populate_goal(
    goal_id: Annotated[str, typer.Argument(help="Active goal id to populate with Practice Items.")],
    target_items_per_lo: Annotated[int, typer.Option("--target-items-per-lo", min=1, help="Desired practicable (non-exam-reserved) Practice Item count per scope LO.")] = 5,
    max_new_per_lo: Annotated[int, typer.Option("--max-new-per-lo", min=1, help="Maximum new Practice Items to ask for per LO.")] = 3,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for practice generation.")] = None,
    review: Annotated[bool, typer.Option("--review", help="Leave the proposal pending review instead of auto-accepting.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling the AI provider.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Generate Practice Items covering an active goal's scope.

    Unlike ``generate-practice``, the completed-probe gate is waived and items
    reserved for the goal's held-out exam do not count as existing supply, so a
    freshly created goal (whose exam pool may have quarantined most of its
    items) becomes practicable in one shot. Auto-accepts the proposal unless
    ``--review`` is passed.
    """

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)

    def _fail(error: str, message: str, **extra: object) -> None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": error, "message": message, **extra}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)

    goal = next((candidate for candidate in loaded.goals if candidate.id == goal_id), None)
    if goal is None or goal.status != "active":
        reason = "not found" if goal is None else f"not active (status={goal.status})"
        _fail("invalid_goal", f"Goal {goal_id} is {reason}.", goal_id=goal_id)
    try:
        plan, at_risk_facets = build_goal_practice_plan(
            loaded,
            repository,
            goal,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
        )
    except PracticeExpansionError as exc:
        _fail("invalid_generation_request", str(exc))
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict(), "at_risk_facets": at_risk_facets}))
        else:
            _echo_practice_generation_plan(plan)
            if at_risk_facets:
                typer.echo(f"At-risk facets in focus: {', '.join(at_risk_facets)}")
        return
    if not plan.targets:
        _fail(
            "no_targets",
            f"Goal {goal_id}'s learning objects already have enough practicable items.",
            plan=plan.as_dict(),
        )
    provider_name, runtime, client = _ready_provider_for_task(
        vault_root,
        loaded.config,
        "authoring",
        ai_provider,
        codex_timeout_seconds=15 * 60,
    )
    if not runtime.ready:
        runtime_status = _runtime_status_for_cli(provider_name, runtime.status)
        runtime_label = "Codex runtime" if provider_name in CODEX_PROVIDER_NAMES else "AI provider"
        _fail(runtime_status, runtime.message or f"{runtime_label} is {runtime_status}.", plan=plan.as_dict())
    try:
        result = generate_goal_practice_proposal(
            vault_root,
            client,
            goal_id=goal_id,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
        )
    except Exception as exc:
        _fail(
            "codex_failed" if provider_name in CODEX_PROVIDER_NAMES else "ai_failed",
            str(exc),
            plan=plan.as_dict(),
        )
    applied_count = 0
    if not review:
        try:
            apply_result = accept_items(vault_root, result.patch_id)
            applied_count = apply_result.applied_count
        except PatchApplicationError as exc:
            _fail("accept_failed", str(exc), proposal_id=result.patch_id, plan=result.plan.as_dict())
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "goal_id": goal_id,
                    "proposal_id": result.patch_id,
                    "accepted": not review,
                    "applied_count": applied_count,
                    "plan": result.plan.as_dict(),
                    "at_risk_facets": at_risk_facets,
                }
            )
        )
    else:
        if review:
            typer.echo(f"Persisted goal-population proposal {result.patch_id}; review it with `proposals`.")
        else:
            typer.echo(f"Populated goal {goal_id}: accepted proposal {result.patch_id} ({applied_count} item(s)).")
        _echo_practice_generation_plan(result.plan)

@app.command("generate-diagnostics")
def generate_diagnostics(
    learning_object_id: Annotated[str | None, typer.Option("--learning-object-id", help="Limit to one Learning Object id.")] = None,
    max_needs: Annotated[int, typer.Option("--max-needs", min=1, help="Maximum pending intervention needs to target.")] = 3,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra diagnostic-generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for diagnostic generation.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling Codex.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    try:
        plan = build_diagnostic_practice_plan(
            loaded,
            repository,
            learning_object_id=learning_object_id,
            max_needs=max_needs,
        )
    except PracticeExpansionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_generation_request", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        else:
            _echo_diagnostic_generation_plan(plan)
        return
    if not plan.targets:
        message = "No pending intervention needs require diagnostic Practice Items."
        if json_output:
            typer.echo(_dump({"version": 1, "error": "no_targets", "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message)
        raise typer.Exit(code=1)
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
    if not runtime.ready:
        runtime_status = _runtime_status_for_cli(provider_name, runtime.status)
        runtime_label = "Codex runtime" if provider_name in CODEX_PROVIDER_NAMES else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime_status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime_status, "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = generate_diagnostic_practice_proposal(
            vault_root,
            client,
            learning_object_id=learning_object_id,
            max_needs=max_needs,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name in CODEX_PROVIDER_NAMES else "ai_failed", "message": str(exc), "plan": plan.as_dict()}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_id": result.patch_id, "plan": result.plan.as_dict(), "fulfilled_need_ids": result.fulfilled_need_ids}))
    else:
        typer.echo(f"Persisted diagnostic-generation proposal {result.patch_id}.")
        _echo_diagnostic_generation_plan(result.plan)

@app.command("debug-advance")
def debug_advance(
    days: Annotated[int, typer.Argument(help="Number of days to advance the vault's derived learning state.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Debug-only: simulate time passing by aging SQLite learning-state timestamps."""

    try:
        result = advance_vault_days(_root(vault), days)
    except DebugAdvanceError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_debug_advance", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "debug_advance": result.as_dict()}))
    else:
        typer.echo(
            f"Advanced vault by {result.days} day(s): shifted "
            f"{result.shifted_cells} timestamp value(s) in derived SQLite state."
        )

@app.command("rebuild-derived-state")
def rebuild_derived_state_command(
    learning_objects: Annotated[
        list[str] | None,
        typer.Option("--learning-object", help="Learning Object id to rebuild. Can be repeated."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Replay persisted attempt logs to rebuild derived learning state."""

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    result = rebuild_all_derived_state(
        loaded,
        repository,
        learning_object_ids=learning_objects,
    )
    if json_output:
        # Preserve the original command's JSON contract while the umbrella
        # internally rebuilds every registered projection and writes one receipt.
        rebuild_payload = {
            "algorithm_version": result.algorithm_version,
            "rebuilt_learning_objects": result.rebuilt_learning_objects,
            "replayed_attempts": result.replayed_attempts,
            "learning_object_ids": result.learning_object_ids,
        }
        if result.marker_id is not None:
            rebuild_payload["marker_id"] = result.marker_id
        typer.echo(_dump({"version": 1, "rebuild": rebuild_payload}))
    else:
        typer.echo(
            f"Rebuilt {result.rebuilt_learning_objects} Learning Object(s), "
            f"replayed {result.replayed_attempts} attempt(s), "
            f"algorithm_version={result.algorithm_version}."
        )

@app.command("rebuild")
def rebuild_command(
    shadow: Annotated[
        bool,
        typer.Option("--shadow", help="Replay on a scratch database and report semantic deltas."),
    ] = False,
    set_values: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            help="Candidate config override as dotted.path=value. Can be repeated.",
        ),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Evaluate a candidate whole-history rebuild without changing live state."""

    if not shadow:
        message = "--shadow is required; use rebuild-derived-state for a live rebuild"
        if json_output:
            typer.echo(_dump({"version": 1, "error": "shadow_required", "message": message}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=2)

    loaded = load_vault(_root(vault))
    try:
        result = shadow_rebuild(loaded, assignments=set_values or ())
    except ShadowRebuildError as exc:
        if json_output:
            typer.echo(
                _dump(
                    {
                        "version": 1,
                        "error": "shadow_rebuild_failed",
                        "message": str(exc),
                    }
                )
            )
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(_dump({"version": 1, "shadow_rebuild": result.as_dict()}))
        return
    summary = result.learner_state_diff["summary"]
    typer.echo(
        "Shadow rebuild complete: "
        f"algorithm_version={result.candidate_algorithm_version}; "
        f"mastery={summary['mastery']}, facet={summary['facet']}, "
        f"schedule={summary['schedule']} semantic change(s)."
    )
    typer.echo(
        "Live database unchanged "
        f"(sha256={result.live_database_sha256_after})."
    )

@app.command("recall-calibration")
def recall_calibration(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    assert_bands: Annotated[bool, typer.Option("--assert", help="Exit non-zero when a severity band fails.")] = False,
) -> None:
    """Developer harness for recall-coverage intervention calibration scenarios."""

    rows = run_recall_calibration_harness()
    if assert_bands:
        try:
            assert_recall_calibration_bands(rows)
        except AssertionError as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "calibration_failed", "message": str(exc), "rows": [row.as_dict() for row in rows]}))
            else:
                typer.echo(format_recall_calibration_table(rows))
                typer.echo(str(exc), err=True)
            raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "rows": [row.as_dict() for row in rows]}))
    else:
        typer.echo(format_recall_calibration_table(rows))

@app.command("observation-templates")
def observation_templates(
    include_all: Annotated[bool, typer.Option("--all", help="Include inactive templates.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    repository = _repository(_root(vault))
    templates = [
        _observation_template_payload(template)
        for template in repository.observation_templates(active_only=not include_all)
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "observation_templates": templates}))
        return
    if not templates:
        typer.echo("No observation templates.")
        return
    for template in templates:
        active = "active" if template["active"] else "inactive"
        emits = "emits attempt" if template["emits_attempt"] else "observation only"
        typer.echo(
            f"{template['id']} {template['domain']} v{template['version']} "
            f"{active} - {template['title']} ({emits})"
        )

@app.command("register-observation-template")
def register_observation_template_command(
    file: Annotated[Path, typer.Option("--file", help="Observation template YAML or JSON.")],
    domain: Annotated[str, typer.Option("--domain", help="Template domain.")],
    version: Annotated[str, typer.Option("--version", help="Template version.")],
    title: Annotated[str, typer.Option("--title", help="Template title.")],
    active: Annotated[bool, typer.Option("--active/--inactive", help="Whether the template is active.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    repository = _repository(vault_root)
    try:
        template_yaml = _observation_template_yaml(file)
        template_id = register_observation_template(
            repository,
            domain=domain,
            version=version,
            title=title,
            template_yaml=template_yaml,
            active=active,
        )
        template = repository.fetch_observation_template(template_id)
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_observation_template", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if template is None:
        raise typer.Exit(code=1)
    payload = _observation_template_payload(template)
    if json_output:
        typer.echo(_dump({"version": 1, "observation_template": payload}))
    else:
        typer.echo(f"Registered observation template {payload['id']}.")

@app.command("record-observation")
def record_observation_command(
    template_id: Annotated[str, typer.Argument(help="Observation template id.")],
    response_json: Annotated[str | None, typer.Option("--response-json", help="Observation response JSON object.")] = None,
    response_file: Annotated[Path | None, typer.Option("--response-file", help="Observation response YAML or JSON.")] = None,
    subject: Annotated[str | None, typer.Option("--subject", help="Related subject id.")] = None,
    learning_object_id: Annotated[
        str | None,
        typer.Option("--learning-object-id", help="Resolved Learning Object binding."),
    ] = None,
    practice_item_id: Annotated[
        str | None,
        typer.Option("--practice-item-id", help="Resolved Practice Item binding."),
    ] = None,
    session_id: Annotated[str | None, typer.Option("--session-id", help="Related session id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    try:
        result = record_observation(
            loaded,
            repository,
            template_id=template_id,
            response=_parse_observation_response(response_json, response_file),
            related_learning_object_id=learning_object_id,
            related_practice_item_id=practice_item_id,
            session_id=session_id,
            subject=subject,
        )
    except (ObservationTemplateError, AttemptValidationError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_observation", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    payload = _observation_result_payload(result)
    if json_output:
        typer.echo(_dump({"version": 1, "observation": payload}))
    else:
        emitted = f", emitted attempt {payload['emitted_attempt_id']}" if payload["emitted_attempt_id"] else ""
        typer.echo(
            f"Recorded observation {payload['observation_event_id']} "
            f"binding={payload['binding_mode']}{emitted}."
        )

@app.command("misconception-candidates")
def misconception_candidates(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id to attach a misconception to.")],
    query: Annotated[str | None, typer.Option("--query", help="Fuzzy-match text as the learner types.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum candidates to surface.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Rank error-type candidates for the self-grade misconception picker (spec §12.5)."""

    loaded = load_vault(_root(vault))
    item = loaded.practice_items.get(practice_item_id)
    if item is None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "not_found", "practice_item_id": practice_item_id}))
        else:
            typer.echo(f"No Practice Item found for {practice_item_id}.", err=True)
        raise typer.Exit(code=1)
    candidates = rank_error_type_candidates(loaded, item=item, query=query, limit=limit)
    if json_output:
        typer.echo(_dump({"version": 1, "candidates": candidates}))
        return
    if not candidates:
        typer.echo("No error types in the taxonomy yet.")
        return
    for candidate in candidates:
        kind = "misconception" if candidate.is_misconception else "error"
        typer.echo(
            f"{candidate.error_type} ({kind}) - {candidate.title} "
            f"[closeness={candidate.closeness:.2f} score={candidate.score:.2f}]"
        )

@app.command("misconception-gate-backfill")
def misconception_gate_backfill(
    force: Annotated[bool, typer.Option("--force", help="Re-run and overwrite existing discrimination rows.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Backfill sim discrimination rows for keyed (item, misconception) pairs (spec §6).

    Deterministic grader only (no AI provider). By default respects existing rows;
    ``--force`` re-runs every pair.
    """

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    results = backfill_discrimination_rows(loaded, repository, force=force)

    backfilled: list[Any] = []
    skipped_existing: list[Any] = []
    skipped_unregistered: list[Any] = []
    for result in results:
        if BACKFILL_SKIPPED_UNREGISTERED in result.reasons:
            skipped_unregistered.append(result)
        elif BACKFILL_SKIPPED_EXISTING in result.reasons:
            skipped_existing.append(result)
        else:
            backfilled.append(result)

    summary = {
        "backfilled": len(backfilled),
        "skipped_existing": len(skipped_existing),
        "skipped_unregistered": len(skipped_unregistered),
    }
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "backfilled": [r.as_dict() for r in backfilled],
                    "skipped_existing": [r.as_dict() for r in skipped_existing],
                    "skipped_unregistered": [r.as_dict() for r in skipped_unregistered],
                    "summary": summary,
                }
            )
        )
        return
    if not results:
        typer.echo("No keyed (item, misconception) pairs found.")
        return
    for result in backfilled:
        verdict = "accepted" if result.accepted else "rejected"
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: {verdict} "
            f"[sens_lb={result.sensitivity_lb():.2f} spec_lb={result.specificity_lb():.2f}]"
        )
    for result in skipped_existing:
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: skipped (existing row) "
            f"[sens_lb={result.sensitivity_lb():.2f} spec_lb={result.specificity_lb():.2f}]"
        )
    for result in skipped_unregistered:
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: skipped (misconception not registered)"
        )
    typer.echo(
        f"Backfilled {summary['backfilled']}, "
        f"skipped {summary['skipped_existing']} existing, "
        f"{summary['skipped_unregistered']} unregistered."
    )

@app.command()
def attempt(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id.")],
    answer: Annotated[str | None, typer.Option("--answer", help="Learner answer markdown.")] = None,
    criterion_points: Annotated[str | None, typer.Option("--criterion-points", help="Comma-separated criterion=points pairs.")] = None,
    fatal_errors: Annotated[str | None, typer.Option("--fatal-errors", help="Comma-separated fatal rubric error ids.")] = None,
    confidence: Annotated[int, typer.Option("--confidence", min=1, max=5, help="Self-grade confidence 1..5.")] = 3,
    attempt_type: Annotated[str | None, typer.Option("--attempt-type", help="Attempt type. Defaults to the first recording type allowed by the item.")] = None,
    hints_used: Annotated[int, typer.Option("--hints-used", min=0, help="Number of hints used.")] = 0,
    error_type: Annotated[str | None, typer.Option("--error-type", help="Optional error taxonomy id or literal.")] = None,
    session_id: Annotated[str | None, typer.Option("--session-id", help="Related session id.")] = None,
    available_minutes: Annotated[int | None, typer.Option("--available-minutes", help="Remaining session minutes.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for grading.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    item = loaded.practice_items.get(practice_item_id)
    if item is None:
        typer.echo(f"No Practice Item found for {practice_item_id}.", err=True)
        raise typer.Exit(code=1)
    rubric = loaded.rubric_for_item(item)
    answer_text = answer if answer is not None else typer.prompt("Answer", default="")
    points = _parse_points(criterion_points)
    if not points and rubric is not None:
        for criterion in rubric.criteria:
            raw = typer.prompt(f"{criterion.id} points", default="0")
            try:
                points[criterion.id] = float(raw)
            except ValueError:
                typer.echo(f"{criterion.id} points must be numeric.", err=True)
                raise typer.Exit(code=1)
    try:
        resolved_attempt_type = attempt_type or default_attempt_type(item.attempt_types_allowed)
        draft = AttemptDraft(
            practice_item_id=practice_item_id,
            learner_answer_md=answer_text,
            attempt_type=resolved_attempt_type,
            hints_used=hints_used,
            session_id=session_id,
        )
        fallback_grade = SelfGradeInput(
            criterion_points=points,
            fatal_errors=_split_items(fatal_errors),
            confidence=confidence,
            error_type=error_type,
        )
        provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "grading", ai_provider)
        if provider_name not in CODEX_PROVIDER_NAMES:
            result = complete_attempt_with_ai_fallback(
                loaded,
                repository,
                draft,
                fallback_grade,
                runtime=runtime,
                ai_client=client if runtime.ready else None,
            )
        else:
            result = complete_attempt_with_codex_fallback(
                loaded,
                repository,
                draft,
                fallback_grade,
                runtime=runtime,
                codex_client=client if runtime.ready else None,
            )
    except (AttemptValidationError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "validation_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    run_post_attempt_pipeline(
        loaded,
        repository,
        result=result,
        session_id=session_id,
        self_grade=fallback_grade,
        ai_client=client if runtime.ready else None,
        available_minutes=available_minutes,
    )
    if json_output:
        typer.echo(_dump({"version": 1, "attempt": result.as_dict()}))
        return
    typer.echo(
        f"Recorded {result.attempt_id}: score={result.rubric_score} "
        f"rating={result.fsrs_rating} due={result.due_at} mastery={result.mastery_mean:.2f}"
    )

@app.command()
def today(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    from learnloop.app_launch import launch_tui

    launch_tui(_root(vault))

@app.command("eval")
def eval_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    section: Annotated[
        str, typer.Option("--section", help="predictions|coverage|gates|retention|propensity|all")
    ] = "all",
    bins: Annotated[int, typer.Option("--bins", help="Calibration bin count.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Calibration report over logged decisions (read-only)."""

    from learnloop.scheduling.evaluation import build_eval_report

    valid = {"predictions", "coverage", "gates", "retention", "propensity"}
    sections = valid if section == "all" else {part.strip() for part in section.split(",") if part.strip()}
    unknown = sections - valid
    if unknown:
        typer.echo(f"Unknown section(s): {', '.join(sorted(unknown))}. Valid: {', '.join(sorted(valid))}.", err=True)
        raise typer.Exit(code=2)
    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    report = build_eval_report(loaded, repository, sections=sections, bins=bins)
    if json_output:
        typer.echo(_dump({"version": 1, "eval": report.as_dict()}))
        return
    typer.echo(report.format_text())

@app.command("exam-calibration")
def exam_calibration_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Report exam prediction/outcome calibration (Brier, log loss, reliability bins)."""

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    report = exam_calibration_report(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_calibration": report}))
        return
    items = report["items"]
    facets = report["facets"]
    typer.echo(
        f"Item predictions: n={items['n']} brier={items['brier']} log_loss={items['log_loss']}"
    )
    typer.echo(f"Facet projections: n={facets['n']} brier={facets['brier']}")

@app.command("probe-coverage")
def probe_coverage_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
) -> None:
    """Hypothesis-contrast / family coverage report (probe redesign §9.5).

    For every decision-relevant hypothesis distinction an episode could
    instantiate, checks that at least two signature-distinct family templates
    can separate it — one direct/minimal and one shifted instrument.
    """

    from learnloop.diagnosis.probe_coverage import family_coverage_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = family_coverage_report(loaded, repository)
    if json_output:
        typer.echo(_dump(report))
        return
    totals = report["totals"]
    typer.echo(
        f"LOs: {totals['learning_objects']} ({totals['learning_objects_with_bindings']} with instrument bindings)"
    )
    typer.echo(
        f"Hypothesis contrasts: {totals['contrasts']} total, "
        f"{totals['contrasts_fully_covered']} fully covered, "
        f"{totals['contrasts_uncovered']} with no separating instrument"
    )
    if totals["integrative_gaps"]:
        typer.echo(f"Integrative/long-form family gaps: {totals['integrative_gaps']} LOs")
    for entry in report["learning_objects"]:
        if not entry["uncovered_contrasts"] and not entry["needs_integrative_family"]:
            continue
        typer.echo(f"- {entry['learning_object_id']}:")
        for pair in entry["uncovered_contrasts"]:
            typer.echo(f"    uncovered: {pair[0]} vs {pair[1]}")
        if entry["needs_integrative_family"]:
            typer.echo("    missing integrative/long-form family")

@app.command("probe-instances")
def probe_instances_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Only this Learning Object's pending episode.")] = None,
    seed: Annotated[int, typer.Option("--seed", help="Deterministic generation seed.")] = 0,
    no_llm: Annotated[bool, typer.Option("--no-llm", help="Skip LLM surfaces; use only parametric templates.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON summary.")] = False,
) -> None:
    """Resolve pending diagnostic episodes through instance generation from
    admitted family/card bindings (probe redesign §10). Surfaces come from the
    configured AI provider when available (§9.2) and fall back to the
    parametric templates."""

    from learnloop.diagnosis.probe_instance_generation import generate_instances_for_episode

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    ai_client = None
    if not no_llm and loaded.config.probe.generation.llm_surfaces:
        resolved = ready_client_for_task(root, loaded.config, "authoring")
        ai_client = resolved.client
    summaries = []
    for lo_id, episode in sorted(repository.open_probe_episodes().items()):
        if episode.status != "pending_items":
            continue
        if learning_object_id is not None and lo_id != learning_object_id:
            continue
        summary = generate_instances_for_episode(
            repository, loaded, episode.id, seed=seed, ai_client=ai_client
        )
        summaries.append(summary.as_dict())
        loaded = load_vault(root)
    if json_output:
        typer.echo(_dump({"version": 1, "episodes": summaries}))
        return
    if not summaries:
        typer.echo("No pending diagnostic episodes to resolve.")
        return
    for summary in summaries:
        generated = summary["generated"]
        typer.echo(
            f"{summary['learning_object_id']}: {len(generated)} instances "
            f"({'unparked' if summary['episode_unparked'] else 'still pending review'})"
        )
        for instance in generated:
            typer.echo(
                f"    {instance['practice_item_id']} [{instance['family_template_id']} "
                f"v{instance['family_template_version']}, {instance['review_status']}, "
                f"{instance.get('generator_id', 'probe_family_parametric')}]"
            )

@app.command("diagnostic-augmentation")
def diagnostic_augmentation_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the full Stage-7 report.")
    ] = False,
) -> None:
    """B1-B4 evaluation licenses and C1-C4 live receipt/revert telemetry."""

    from learnloop.diagnosis.diagnostic_augmentation import (
        diagnostic_augmentation_report,
    )

    repository = _repository(_root(vault))
    report = diagnostic_augmentation_report(repository)
    if json_output:
        typer.echo(_dump(report))
        return
    realism = report["persona_realism"]
    planted = report["planted_evaluation"]
    phase_c = report["phase_c"]
    typer.echo(
        f"persona realism: {realism['runs']} run(s); "
        f"latest={((realism.get('latest') or {}).get('verdict') or 'unavailable')}"
    )
    typer.echo(
        f"planted evaluation: {planted['licensed_runs']}/{planted['runs']} "
        f"licensed run(s), {planted['cases']} case(s)"
    )
    typer.echo(f"Phase C live receipts: {phase_c['live_receipts']}")
    for rung in ("c1", "c2", "c3", "c4"):
        typer.echo(f"  {rung.upper()} hypothesis: {phase_c['hypotheses'][rung]}")
        typer.echo(f"     revert: {phase_c['revert_criteria'][rung]}")

@app.command("persona-realism")
def persona_realism_command(
    personas: Annotated[
        Path,
        typer.Option(
            "--personas",
            help="JSON list of persona trace strings, or {'traces': [...]}.",
        ),
    ],
    generator_provider: Annotated[
        str,
        typer.Option(
            "--generator-provider",
            help="Provider name that authored these persona traces.",
        ),
    ],
    generator_model: Annotated[
        str,
        typer.Option(
            "--generator-model",
            help="Model that authored these persona traces.",
        ),
    ],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    separation_threshold: Annotated[
        float,
        typer.Option("--threshold", help="Separability score that rejects the corpus."),
    ] = 0.70,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Run B2's blinded text-only persona-vs-real matcher and append its license."""

    from learnloop.diagnosis.diagnostic_augmentation import model_family
    from learnloop.content.authoring.persona_realism import match_persona_realism

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    try:
        payload = _stage7_manifest(personas)
        traces = payload.get("traces") if isinstance(payload, Mapping) else payload
        if not isinstance(traces, list) or not all(
            isinstance(trace, str) for trace in traces
        ):
            raise ValueError(
                "persona manifest must be a JSON list of strings or {'traces': [...]}"
            )
        report = match_persona_realism(
            repository,
            traces,
            # Generated-regression personas may only be licensed inside
            # `diagnostic-eval`, which scores the exact same generated corpus.
            # The standalone boundary exists solely for the authoring gate.
            persona_source="authored_signature",
            generator_provider=generator_provider,
            generator_model=generator_model,
            generator_family=model_family(generator_provider, generator_model),
            separation_threshold=separation_threshold,
        )
    except ValueError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_manifest", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump(report.as_dict()))
        return
    typer.echo(
        f"{report.verdict}: persona={report.persona_count}, real={report.real_count}, "
        f"separability={report.balanced_accuracy if report.balanced_accuracy is not None else 'unavailable'}"
    )
    typer.echo(report.note)

@app.command("diagnostic-eval")
def diagnostic_eval_command(
    generator_provider: Annotated[
        str,
        typer.Option(
            "--generator-provider",
            help="Configured provider used only to generate planted traces.",
        ),
    ],
    diagnostician_provider: Annotated[
        str,
        typer.Option(
            "--diagnostician-provider",
            help="Configured provider used only to diagnose blind traces.",
        ),
    ],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    cases_file: Annotated[
        Path | None,
        typer.Option(
            "--cases",
            help="JSON planted-case manifest; defaults to vault discrimination profiles.",
        ),
    ] = None,
    sample_count: Annotated[
        int,
        typer.Option("--sample-count", min=1, help="Independent C3 samples per case."),
    ] = 3,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Commission B1-B3 with separate configured model providers."""

    from learnloop.diagnosis.diagnostic_augmentation import (
        commission_planted_diagnostic_evaluation,
        planted_cases_from_manifest,
    )

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    cases = None
    try:
        if cases_file is not None:
            cases = planted_cases_from_manifest(_stage7_manifest(cases_file))
    except ValueError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_manifest", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    clients: list[Any] = []
    for role, provider_name in (
        ("generator", generator_provider),
        ("diagnostician", diagnostician_provider),
    ):
        runtime = _runtime_for_provider(vault_root, loaded.config, provider_name)
        if not runtime.ready:
            message = (
                f"{role} provider {provider_name!r} is unavailable: "
                f"{getattr(runtime, 'status', 'not ready')}"
            )
            if json_output:
                typer.echo(_dump({"version": 1, "error": "provider_unavailable", "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        clients.append(
            _client_for_provider(vault_root, loaded.config, provider_name)
        )
    report = commission_planted_diagnostic_evaluation(
        loaded,
        repository,
        generator_client=clients[0],
        diagnostician_client=clients[1],
        cases=cases,
        sample_count=sample_count,
    )
    if json_output:
        typer.echo(_dump(report))
        return
    realism = report.get("persona_realism")
    evaluation = report["evaluation"]
    typer.echo(
        "persona realism: "
        + (str(realism["verdict"]) if realism is not None else "not run")
    )
    typer.echo(
        f"diagnostic eval: {evaluation['status']}; "
        f"{evaluation['metrics'].get('cases_by_shape', {})}"
    )

@app.command("scoreboard")
def scoreboard_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    replay: Annotated[
        bool,
        typer.Option(
            "--replay",
            help=(
                "Compute questions_to_certification / certification_regret via "
                "the §5.8.1 prefix replay. Copies the sqlite file per cutoff and "
                "mutates only the copy; costs ~1.5-3s per cutoff, bisected."
            ),
        ),
    ] = False,
    replay_budget: Annotated[
        int,
        typer.Option(
            "--replay-budget",
            min=1,
            help="Maximum prefix-replay evaluations. Exhausting it leaves the two certification metrics unavailable rather than guessed.",
        ),
    ] = None,  # type: ignore[assignment]
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """The frozen §3 B5 scoreboard (spec_diagnostic_augmentation_v1 §3 B5, Meas §5.7).

    Printed in B5's frozen order, `problems_to_cold_success` and
    `harmful_write_rate` first — B5: "a system can raise anchor accuracy while
    becoming slower and more interrogative, and every remaining metric on this
    list would report success."

    A metric with no data prints `unavailable` with the reason. It never prints
    0.0: `harmful_write_rate`'s target IS ~0, so an unproduced metric rendered as
    zero is indistinguishable from a solved problem.
    """

    from learnloop.diagnosis.scoreboard import DEFAULT_REPLAY_BUDGET, scoreboard

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = scoreboard(
        loaded,
        repository,
        replay=replay,
        replay_budget=(
            DEFAULT_REPLAY_BUDGET if replay_budget is None else int(replay_budget)
        ),
    )
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    for metric in report["metrics"]:
        # The companion is indented under its primary so the pair B5 requires
        # reads as a pair rather than as two independent rows.
        lead = "  " if metric["companion_of"] else ""
        if metric["available"]:
            value = f"{metric['value']:.4g}"
        else:
            value = f"unavailable ({metric['availability']})"
        denominator = metric["denominator"]
        over = (
            f" [{metric['numerator']}/{denominator} {metric['denominator_label']}]"
            if denominator is not None
            else ""
        )
        typer.echo(f"{lead}{metric['name']}: {value}{over}")
        if not metric["available"]:
            typer.echo(f"{lead}    {metric['note']}")
    counts = report["availability_counts"]
    typer.echo(
        f"{report['available']}/{len(report['metrics'])} metrics available · "
        + " · ".join(
            f"{arm}={counts[arm]}" for arm in counts if arm != "available" and counts[arm]
        )
    )

@app.command("probe-audit")
def probe_audit_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Probe pilot audit (probe redesign §13, Checkpoint 4): predicted-vs-realized
    EIG, negative realized information, time calibration, cross-surface
    replication, downstream outcomes, regrade agreement, evidence-source
    separation, shadow-policy comparison, and the replay determinism check."""

    from learnloop.diagnosis.probe_audit import pilot_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = pilot_report(loaded, repository)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    eig = report["eig_calibration"]
    typer.echo(
        f"EIG: {eig['observations']} qualifying observations, "
        f"expected {eig['mean_expected_eig']} vs realized {eig['mean_realized_information']} nats, "
        f"negative-information rate {eig['negative_information_rate']}"
    )
    time_report = report["time_calibration"]
    typer.echo(
        f"Time: {time_report['observations']} observations, "
        f"mean error {time_report['mean_error_seconds']}s "
        f"(abs {time_report['mean_absolute_error_seconds']}s)"
    )
    replication = report["cross_surface_replication"]
    typer.echo(
        f"Cross-surface replication: {replication['replicated']}/"
        f"{replication['episodes_with_cross_surface_pairs']} "
        f"(rate {replication['replication_rate']})"
    )
    downstream = report["downstream_outcomes"]
    typer.echo(
        f"Downstream (proxy): {downstream['episodes_with_before_and_after']} measurable episodes, "
        f"mean success delta {downstream['mean_success_delta']}"
    )
    determinism = report["replay_determinism"]
    failures = len(determinism["failures"])
    typer.echo(
        f"Replay determinism: {determinism['episodes_checked']} episodes checked — "
        + ("OK" if determinism["deterministic"] else f"{failures} FAILURES")
    )

@app.command("graph-identifiability")
def graph_identifiability_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject id.")] = None,
    schedule_probes: Annotated[bool, typer.Option("--schedule-probes", help="Persist a discriminating probe / coarsen need per finding (§11.3).")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Assessment identifiability doctor (knowledge-model §11.3).

    Analyzes each subject's criterion-by-facet-capability matrix, recipe
    structure, and compositional records for the seven non-identifiability
    warnings, reporting unresolved bundles rather than false facet-specific
    precision. Findings can be turned into discriminating-probe generation needs.
    """

    from learnloop.learner.identifiability import graph_identifiability_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = graph_identifiability_report(
        loaded, repository, subject_id=subject, schedule_probes=schedule_probes
    )
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    totals = report["totals"]
    typer.echo(
        f"Identifiability: {totals['findings']} non-identifiable distinction(s), "
        f"{totals['scheduled_probes']} discriminating probe(s) scheduled."
    )
    for subject_report in report["subjects"]:
        # Meas §D1 measurement_rank (plan 3.4) is reported for every subject,
        # including one with no findings — an uninstrumented facet costs a
        # dimension without tripping any of the seven checks (§5.8.2). Analysis
        # only: nothing here merges a facet; collapse candidates go to review.
        rank = subject_report.get("measurement_rank") or {}
        head = f"  {subject_report['subject_id']}: {subject_report['counts']['findings']} finding(s)"
        if rank:
            ratio = rank.get("rank_ratio")
            head += (
                f"; measurement rank {rank['independent_dimensions']}/{rank['facets_declared']} facets"
                + (f" ({ratio:.2f})" if isinstance(ratio, float) else "")
            )
        typer.echo(head)
        if rank.get("deficit"):
            typer.echo(
                f"    rank deficit {rank['deficit']}: "
                f"{rank['deficit_from_unobserved']} facet(s) observed by nothing, "
                f"{rank['deficit_from_collapse']} lost to shared measurement signatures"
            )
            for group in rank["collapsed_groups"]:
                typer.echo(f"    indistinguishable (review, never auto-merge): {', '.join(group)}")
        for bundle in subject_report["unresolved_bundles"]:
            typer.echo(f"    [check {bundle['check']}] {bundle['message']}")

@app.command("residual-diagnostics")
def residual_diagnostics_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Residual-dependence diagnostics (knowledge-model §8.4).

    Report-only, deterministic structure hints from residual dependence between
    facets sharing tasks, systematic combined-task failure, context-specific
    residuals, and indistinguishable response signatures. Never mutates structure.
    """

    from learnloop.learner.residual_diagnostics import residual_dependence_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = residual_dependence_report(loaded, repository, subject_id=subject)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(
        f"Residual diagnostics: {report['totals']['suggestions']} structure suggestion(s) "
        f"across {report['totals']['facet_pairs']} co-tasked facet pair(s)."
    )
    for suggestion in report["suggestions"]:
        typer.echo(f"  [{suggestion['kind']}] {suggestion['message']}")

@app.command("probe-regrade")
def probe_regrade_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum observations to regrade.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON summary.")] = False,
) -> None:
    """Re-grade a sample of probe observations and record grader agreement per
    family and grader version (probe redesign §7.6, Checkpoint 4.4).
    Non-destructive: original evidence is never superseded."""

    from learnloop.diagnosis.probe_audit import grading_confusion_report, run_probe_regrade_checks

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    resolved = ready_client_for_task(root, loaded.config, "grading")
    provider_name, client = resolved.provider_name, resolved.client
    if client is None:
        typer.echo(f"Grading provider {provider_name} is unavailable; cannot regrade.")
        raise typer.Exit(code=1)
    summary = run_probe_regrade_checks(loaded, repository, client, limit=limit)
    report = grading_confusion_report(repository)
    if json_output:
        typer.echo(_dump({"version": 1, "run": summary, "confusion": report}))
        return
    typer.echo(
        f"Regraded {summary['recorded']}/{summary['attempted']} sampled observations "
        f"({summary['failed']} failed)."
    )
    for key, scope in report["scopes"].items():
        typer.echo(f"- {key}: agreement {scope['agreement_rate']} over {scope['checks']} checks")

@app.command("taxonomy-regrade-check")
def taxonomy_regrade_check_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum attempts to regrade.")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
) -> None:
    """Non-destructive mechanism-taxonomy regrade check (knowledge-model §10.1/§16).

    Re-grades a sample of graded attempts under the current GRADING_PROMPT_VERSION
    and reports whether any error-type attribution regresses when compared through
    the §10.1 legacy map. Writes no belief state. Exits non-zero on a regression."""

    from learnloop.diagnosis.taxonomy_regrade import run_taxonomy_regrade_checks

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    resolved = ready_client_for_task(root, loaded.config, "grading")
    provider_name, client = resolved.provider_name, resolved.client
    if client is None:
        typer.echo(f"Grading provider {provider_name} is unavailable; cannot regrade.")
        raise typer.Exit(code=1)
    report = run_taxonomy_regrade_checks(loaded, repository, client, limit=limit)
    if json_output:
        typer.echo(_dump({"version": 1, "report": report}))
    else:
        typer.echo(
            f"Taxonomy regrade check under {report['prompt_version']}: "
            f"checked {report['checked']}/{report['attempted']} attempts, "
            f"{report['regression_count']} regressions ({report['failed']} failed)."
        )
        for regression in report["regressions"]:
            typer.echo(
                f"- {regression['attempt_id']}: dropped "
                f"{', '.join(regression['dropped_mechanisms'])}"
            )
    if not report["no_regressions"]:
        raise typer.Exit(code=1)

@app.command("causal-selection-readiness")
def causal_selection_readiness_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
) -> None:
    """WP0 readiness for the formal causal selector (decision-value spec §8 Stage 0).

    Candidate multiplicity, likelihood-regime counts, duration-source shares,
    shadow conversion counts, and repair-linked cold-outcome volume — every
    empty denominator as a typed unavailable arm, never a favorable zero.
    """

    from learnloop.diagnosis.causal_selection_audit import causal_selection_readiness

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = causal_selection_readiness(loaded, repository)
    if json_output:
        typer.echo(_dump(report))
        return
    factors = report["factors"]
    typer.echo(f"factors · total={factors['total']} open={factors['open']}")
    for key in ("candidate_multiplicity", "likelihood_regimes"):
        block = report[key]
        if not block.get("available"):
            typer.echo(f"{key} · unavailable ({block['reason']})")
        else:
            counts = ", ".join(
                f"{arm}={count}" for arm, count in sorted(block["counts"].items())
            )
            typer.echo(f"{key} · {counts}")
    durations = report["duration_sources"]
    if durations.get("available"):
        shares = ", ".join(
            f"{source}={count}"
            for source, count in sorted(durations["source_counts"].items())
        )
        typer.echo(
            f"duration_sources · {shares} · distinct_values="
            f"{durations['distinct_minute_values']} · pooled_latency_n="
            f"{durations['pooled_latency']['sample_count']}"
        )
    else:
        typer.echo(f"duration_sources · unavailable ({durations['reason']})")
    shadows = report["shadow_conversions"]
    if shadows.get("available"):
        typer.echo(
            f"shadow · receipts={shadows['receipts']} formal_available="
            f"{shadows['formal_arm_available']} would_change(measure="
            f"{shadows['would_change_measure_vs_repair']}, candidate="
            f"{shadows['would_change_candidate']}, repair="
            f"{shadows['would_change_repair']}) full_vs_equal(comparable="
            f"{shadows['full_vs_equal_cost_comparable']}, diverged="
            f"{shadows['full_vs_equal_cost_diverged']})"
        )
    else:
        typer.echo(f"shadow · unavailable ({shadows['reason']})")
    cold = report["cold_outcomes"]
    if cold.get("available"):
        outcomes = ", ".join(
            f"{arm}={count}" for arm, count in sorted(cold["outcomes"].items())
        )
        typer.echo(
            f"cold_outcomes · {outcomes} · training_eligible={cold['training_eligible']}"
        )
    else:
        typer.echo(f"cold_outcomes · unavailable ({cold['reason']})")
    typer.echo(f"note · {report['expectations_note']}")
    for finding in report["findings"]:
        typer.echo(f"finding · {finding['kind']}: {finding['parameter']}")

@app.command("causal-attribution-audit")
def causal_attribution_audit_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
) -> None:
    """Show P0 attribution fill, abstention, and firewall telemetry.

    Also reports the A5 missing-vocabulary capture and the two-tailed causal-lane
    fill/abstention rates: standing constraint 2 requires watching BOTH tails,
    and an abstention rate nobody reads is not a signal.
    """

    from learnloop.diagnosis.causal_health import causal_lane_health
    from learnloop.attempts.grading import causal_attribution_audit_report
    from learnloop.diagnosis.missing_vocabulary import missing_vocabulary_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = causal_attribution_audit_report(repository)
    vocabulary = missing_vocabulary_report(repository)
    lane_health = causal_lane_health(repository)
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 2,
                    "report": report,
                    "missing_vocabulary": vocabulary,
                    "lane_health": lane_health,
                }
            )
        )
        return
    if not report["groups"]:
        typer.echo("No causal-attribution telemetry has been recorded.")
    for group in report["groups"]:
        typer.echo(
            f"{group['prompt_version']} · {group['model']}: "
            f"{group['attributions']} attributions across {group['attempts']} attempts; "
            f"resolved={group['resolution_counts']['resolved']}, "
            f"unresolved={group['resolution_counts']['unresolved']}, "
            f"abstained={group['resolution_counts']['abstained']}, "
            f"firewall={group['firewall_trigger_count']}"
        )
        # Meas §3.A5's own two tails, on the same grouping key. Printed even at
        # zero: a tail that disappears from the report when it is empty cannot be
        # watched, and "collapsed toward zero" is the thing being watched.
        profiles = group.get("discrimination_profile_counts") or {}
        if any(profiles.values()):
            typer.echo(
                "  profiles · "
                + ", ".join(f"{arm}={count}" for arm, count in sorted(profiles.items()))
            )
    typer.echo(
        f"vocabulary · abstention_rate={vocabulary['abstention_rate']:.3f} "
        f"({vocabulary['abstentions']}/{vocabulary['attributions']} attributions) · "
        f"{vocabulary['notes']} missing-vocabulary notes"
    )
    for source, count in sorted((vocabulary["by_source"] or {}).items()):
        reasons = ", ".join(
            f"{reason}={value}"
            for reason, value in sorted(
                (vocabulary["by_reason"].get(source) or {}).items()
            )
        )
        typer.echo(f"  {source}: {count} · {reasons}")
    if vocabulary["uncaptured_diagnostic_abstentions"]:
        # The one hole this store cannot heal after the fact.
        typer.echo(
            "  WARNING: "
            f"{vocabulary['uncaptured_diagnostic_abstentions']} diagnostic "
            "abstention(s) predate the note store and cannot be backfilled"
        )
    for channel in lane_health["channels"]:
        typer.echo(
            f"lane · {channel['channel']}: {channel['tail']} · "
            f"fill={channel['fill_rate']:.3f} · "
            f"abstain={channel['abstention_rate']:.3f} · "
            f"missing={channel['missing']}/{channel['total']}"
        )

@app.command("instrument-audit")
def instrument_audit_command(
    since: Annotated[
        str | None,
        typer.Option("--since", help="ISO-8601 lower bound on created_at."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write the JSON report to a file.")
    ] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Read every Meas §3 instrument class's REVERT criterion (plan item 6.4).

    §3 requires each instrument class to state a hypothesis and a revert
    criterion, and the plan requires the criterion to be measurable with shipped
    code — "a rung kept on judgement is exactly what the spec forbids". This is
    the one command that reads all four:

    * A2 laddered stems — cross-column vs within-column outcome agreement on one
      stem. Revert when the two are equal (the independence claim is false).
    * A3 error hunts — agreement between error-hunt and constructed-response
      outcomes on the same facet. Revert when they are uncorrelated (the
      instrument measures proofreading).
    * A4 contrast pairs — share of within-pair differences explained by serving
      order, plus the realized balance of the randomization that licenses it.
      Revert when order dominates.
    * A5 discrimination profiles — the two-tailed profile rejection rate. Revert
      when `no_profile_applies` collapses toward zero, and treat a profile
      matching nearly every failure as equally suspect.

    Every arm reports its availability honestly: a rate over too little data is
    `no_data` with the counts visible, never a 0.0 or a 1.0.
    """

    from learnloop.diagnosis.contrast_pairs import contrast_pair_order_effect
    from learnloop.diagnosis.discrimination_profiles import (
        profile_coverage,
        profile_match_fill_rate,
    )
    from learnloop.diagnosis.error_hunt import error_hunt_outcome_summary, proofreading_signal
    from learnloop.content.authoring.laddered_stems import stem_independence_signal, stem_shapes

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    metrics = [
        stem_independence_signal(loaded, repository, since=since),
        proofreading_signal(loaded, repository, since=since),
        contrast_pair_order_effect(loaded, repository, since=since),
        profile_match_fill_rate(repository, since=since),
    ]
    payload = {
        "version": 1,
        "since": since,
        "metrics": [metric.as_dict() for metric in metrics],
        # Companions, so a healthy-looking rate can be read against the pool it
        # was computed over. A rejection rate of 0.4 over three profiled items
        # says almost nothing, and the reader should be able to see that here.
        "discrimination_profile_coverage": profile_coverage(loaded),
        "error_hunt_outcomes": error_hunt_outcome_summary(repository, since=since),
        "laddered_stems": [shape.as_dict() for shape in stem_shapes(loaded)],
    }
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    for metric in metrics:
        verdict = metric.detail.get("verdict", "-")
        value = "-" if metric.value is None else f"{metric.value:.3f}"
        typer.echo(
            f"{metric.name}: {metric.availability} · value={value} "
            f"({metric.numerator or 0:g}/{metric.denominator or 0:g} "
            f"{metric.denominator_label}) · verdict={verdict}"
        )
        typer.echo(f"  {metric.note}")
    coverage = payload["discrimination_profile_coverage"]
    typer.echo(
        f"profiles: {coverage['profiles']} on {coverage['items_with_profiles']}"
        f"/{coverage['practice_items']} item(s); "
        f"{coverage['unlinked_authored_profiles']} unlinked to the registry"
    )
    hunts = payload["error_hunt_outcomes"]
    typer.echo(
        f"error hunts: {hunts['attempts']} attempt(s), "
        f"{hunts['clean_solution_attempts']} on clean solutions, "
        f"{hunts['planted_repaired']} plant(s) repaired, "
        f"{hunts['misconception_candidates_written']} misconception candidate(s)"
    )
    ladders = [shape for shape in payload["laddered_stems"] if shape["is_ladder"]]
    typer.echo(
        f"laddered stems: {len(ladders)} ladder(s) over "
        f"{len(payload['laddered_stems'])} stem(s)"
    )

@app.command("commission-contrast-pairs")
def commission_contrast_pairs_command(
    subject: Annotated[
        str | None, typer.Option("--subject", help="Restrict to one subject id.")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write the JSON report to a file.")
    ] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Turn identifiability findings into A4 contrast-pair authoring requests.

    Meas §3.A4: contrast pairs are "commissioned, not merely permitted —
    ``analyze_identifiability`` already finds facet pairs no instrument separates,
    and those findings become contrast-pair authoring requests."

    Read-only, like `contract-commissioning`: it derives a queue and nothing else.
    Deferred findings stay IN the queue with a typed reason rather than being
    dropped, because a queue that silently omits its uncommissionable rows is how
    an obligation goes unnoticed for months.
    """

    from learnloop.diagnosis.contrast_pairs import commission_contrast_pairs

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    plan = commission_contrast_pairs(loaded, repository, subject_id=subject)
    payload = plan.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    summary = payload["summary"]
    typer.echo(
        f"Contrast pairs: {summary['commissioned']} commissioned, "
        f"{summary['deferred']} deferred, over {summary['queue_length']} finding(s)."
    )
    for request in plan.commissioned:
        typer.echo(
            f"  COMMISSION {'/'.join(request.facet_ids)} "
            f"(check {request.finding.check}, {request.finding.detail})"
        )
    for request in plan.deferred:
        typer.echo(
            f"  {request.disposition} {request.finding.target_key}: {request.reason}"
        )

@app.command("cold-probe-schedule")
def cold_probe_schedule_command(
    learning_object: Annotated[
        str | None,
        typer.Option("--lo", help="Schedule one Learning Object instead of the whole vault."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Queue the delayed cold probe for each certified LO (measurement §5.7).

    One held-out-surface item per certified LO, due at the fitted horizon after
    certification (default: +2 weeks, expiring at +3 weeks). Idempotent — a
    certificate that already has a probe, consumed or expired, is not re-probed.
    A certificate that has since been withdrawn schedules nothing and has any
    queued probe cancelled.
    """

    from learnloop.goals.certification_cold_probe import (
        schedule_certification_cold_probes,
    )

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = schedule_certification_cold_probes(
        loaded, repository, learning_object_id=learning_object
    )
    payload = report.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    counts = payload["counts"]
    typer.echo(
        f"Cold probes: {counts['scheduled']} scheduled, "
        f"{counts['already_scheduled']} already queued, "
        f"{counts['not_certified']} LO(s) not certified, "
        f"{counts['withdrawn_probe_cancelled']} cancelled on withdrawal"
    )
    # `no_servable_item` belongs in this sum for the same reason as the other
    # two: the certificate has no probe it can actually administer, so
    # false_certification_rate cannot see it. It is counted here rather than
    # silently dropped, which is what an unlisted third arm would have done.
    unmeasurable = (
        counts["no_held_out_surface"]
        + counts["no_candidate_item"]
        + counts["no_servable_item"]
    )
    if unmeasurable:
        # Louder than a count in a table: a certificate with no held-out surface
        # is UNMEASURABLE, which is worse news than unmeasured (§5.7 has no other
        # external validity check to fall back on).
        typer.echo(
            f"  WARNING: {unmeasurable} certificate(s) have no held-out surface "
            "to probe with — false_certification_rate cannot see them"
        )
    for decision in payload["decisions"]:
        if decision["decision"] in {"not_certified", "already_scheduled"}:
            continue
        suffix = (
            f" -> {decision['practice_item_id']} due {decision['not_before']}"
            if decision["practice_item_id"]
            else ""
        )
        typer.echo(f"  {decision['learning_object_id']}: {decision['decision']}{suffix}")

@app.command("cold-probe-audit")
def cold_probe_audit_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """`false_certification_rate` and the coverage of the probe lane (§5.7).

    "The alpha actually being run at, and the only number that licenses any
    speed claim." Over zero scored probes it reports UNAVAILABLE, never 0.0: a
    rate of zero with an empty denominator reads as "no certificate has ever been
    false" when the truth is "no certificate has ever been checked".
    """

    from learnloop.goals.certification_cold_probe import (
        certification_cold_probe_report,
    )

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = certification_cold_probe_report(loaded, repository)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    metric = report["false_certification_rate"]
    arms = metric["arms"]
    if metric["status"] == "unavailable":
        typer.echo(
            "false_certification_rate: UNAVAILABLE "
            f"({metric['unavailable_reason']}) — denominator 0; "
            f"{arms['awaiting_probe']} probe(s) awaiting, "
            f"{arms['probe_expired']} expired, "
            f"{arms['indeterminate']} indeterminate"
        )
    else:
        typer.echo(
            f"false_certification_rate: {metric['value']:.3f} "
            f"= {metric['numerator']}/{metric['denominator']} "
            f"(held {arms['held']}, failed {arms['failed']}); "
            f"{arms['awaiting_probe']} awaiting, "
            f"{arms['probe_expired']} expired, "
            f"{arms['indeterminate']} indeterminate"
        )
    for reason, count in sorted((metric["indeterminate_reasons"] or {}).items()):
        typer.echo(f"  indeterminate · {reason}: {count}")
    coverage = report["coverage"]
    typer.echo(
        f"Coverage: {coverage['certificates_active']} active certificate(s), "
        f"{coverage['certificates_unscheduled']} unscheduled, "
        f"{coverage['certificates_unmeasurable']} unmeasurable"
    )
    for row in report["certificates"]:
        detail = row["verdict"] or row["probe_status"]
        if row["unschedulable_reason"]:
            detail = f"{detail} ({row['unschedulable_reason']})"
        typer.echo(
            f"  {row['learning_object_id']}: {detail} "
            f"[{row['certified_cells']} cell(s), certified {row['certified_at']}]"
        )
    typer.echo(f"Cold-outcome labels available to causal P4: {report['cold_outcome_labels']}")

@app.command("commission-causal-probes")
def commission_causal_probes_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    factor: Annotated[
        str | None,
        typer.Option("--factor", help="Commission one factor instead of draining the queue."),
    ] = None,
    item: Annotated[
        str | None,
        typer.Option("--item", help="Force a candidate PracticeItem id as the instrument."),
    ] = None,
    reviewer_verdict: Annotated[
        Path | None,
        typer.Option(
            "--adversarial-review",
            help=(
                "JSON file with the independent manipulation review "
                "(contract_consistent, measurement_target_independence, "
                "undeclared_differences). Without it the audit lands "
                "pending_adversarial_review and nothing is minted."
            ),
        ),
    ] = None,
    reviewer_id: Annotated[
        str | None,
        typer.Option("--reviewer-id", help="Reviewer identity for the audit (must differ from the generator)."),
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", min=1, help="Maximum factors to commission in one run.")
    ] = 4,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
) -> None:
    """Commission discriminating probe instruments for divergent causal factors.

    Drains the `causal_probe_instrument_commissioning` machine-check queue (Stage
    2.1). The blind prediction bundles map each hypothesis's typed target onto
    the fresh candidate item's authored criterion targets and run no model;
    observation-conditioned postdictive claims are excluded per causal §5.1.
    Commissioning stops at `registered`:
    reviewing and activating an instrument is a separate, deliberate act — see
    `review-causal-probe`.
    """

    from learnloop.diagnosis.causal_orchestrator import (
        MACHINE_CHECK_INSTRUMENT_COMMISSIONING,
        resolve_machine_check,
    )
    from learnloop.diagnosis.causal_probe_commissioning import (
        COMMISSIONING_POLICY_VERSION,
        commission_probe_instrument,
    )

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    review = None
    if reviewer_verdict is not None:
        review = jsonlib.loads(reviewer_verdict.read_text(encoding="utf-8"))
    queued: list[tuple[str, str | None]] = []
    if factor:
        queued = [(factor, None)]
    else:
        queued = [
            (str(check["factor_id"]), str(check["id"]))
            for check in repository.causal_machine_checks(status="pending")
            if str(check["kind"]) == MACHINE_CHECK_INSTRUMENT_COMMISSIONING
            and check.get("factor_id")
        ][:limit]
    results: list[dict[str, Any]] = []
    for factor_id, check_id in queued:
        result = commission_probe_instrument(
            loaded,
            repository,
            factor_id=factor_id,
            candidate_practice_item_id=item,
            adversarial_review=review,
            reviewer_agent_run_id=reviewer_id,
            generation_agent_run_id="learnloop_commission_cli",
        )
        if check_id and result["outcome"] in {"commissioned", "already_available"}:
            # Discharge the obligation explicitly, with grounds. The sweep would
            # eventually close it as "obligation_no_longer_present", which says
            # nothing about what satisfied it.
            resolve_machine_check(
                repository,
                check_id,
                resolution={
                    "basis": "instrument_commissioned",
                    "candidate_id": result.get("candidate_id"),
                    "practice_item_id": result.get("practice_item_id"),
                    "policy_version": COMMISSIONING_POLICY_VERSION,
                },
            )
        results.append({"factor_id": factor_id, **result})
    if json_output:
        typer.echo(_dump({"version": 1, "results": results}))
        return
    if not results:
        typer.echo("No factor owes a discriminating instrument.")
        return
    for result in results:
        detail = result.get("candidate_id") or result.get("manipulation_audit_id") or ""
        typer.echo(
            f"{result['factor_id']} · {result['outcome']}"
            + (f" · {detail}" if detail else "")
            + (
                f" · item={result['practice_item_id']}"
                if result.get("practice_item_id")
                else ""
            )
        )

@app.command("review-causal-probe")
def review_causal_probe_command(
    candidate_id: Annotated[str, typer.Argument(help="Causal probe candidate id.")],
    to_status: Annotated[
        str,
        typer.Option("--to", help="registered | reviewed | active | rejected."),
    ],
    reviewer: Annotated[
        str | None, typer.Option("--reviewer", help="Reviewer identity (required to review or reject).")
    ] = None,
    reason: Annotated[str | None, typer.Option("--reason", help="Audit reason for the transition.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Walk a commissioned probe up the register → review → activate ladder.

    Only an ACTIVE candidate is servable, and only a reviewer may move one past
    `registered` — the gate exists because a blind bundle's complement
    declarations are pre-registered commitments a human should see before the
    instrument buys learner time.
    """

    from learnloop.diagnosis.causal_probe_coherence import transition_probe_candidate

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    updated = transition_probe_candidate(
        repository,
        candidate_id,
        to_status=to_status,
        reviewer=reviewer,
        reason=reason,
    )
    typer.echo(
        f"{updated['id']} · {updated['status']} · item={updated['practice_item_id']}"
        + (f" · reviewer={updated['reviewer']}" if updated.get("reviewer") else "")
    )

@app.command("build-causal-taxonomy")
def build_causal_taxonomy_command(
    vault: Annotated[
        Path | None, typer.Option("--vault", help="Vault root.")
    ] = None,
    min_cluster_size: Annotated[
        int,
        typer.Option(
            "--min-cluster-size",
            min=2,
            help=(
                "Minimum observations sharing a repair equivalence and "
                "discrimination profile required to mint a mechanism."
            ),
        ),
    ] = 2,
    activate: Annotated[
        bool,
        typer.Option(
            "--activate/--draft",
            help="Make this immutable snapshot eligible for new receipts.",
        ),
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the full JSON artifact.")
    ] = False,
) -> None:
    """Build the P1 mechanism taxonomy as an explicit maintenance batch."""

    from learnloop.diagnosis.causal_attribution import (
        mint_causal_mechanism_taxonomy,
    )

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    taxonomy = mint_causal_mechanism_taxonomy(
        repository,
        min_cluster_size=min_cluster_size,
        activate=activate,
    )
    retired = repository.retired_causal_mechanism_taxonomy_versions()
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "taxonomy": taxonomy,
                    "retired_versions": retired,
                }
            )
        )
        return
    typer.echo(
        f"{taxonomy['id']} · {taxonomy['status']} · "
        f"{len(taxonomy['taxonomy'].get('clusters') or [])} mechanisms · "
        f"{len(taxonomy.get('assignments') or [])} assignments"
    )
    for cluster in taxonomy["taxonomy"].get("clusters") or []:
        typer.echo(
            f"  {cluster['id']} · {cluster.get('label') or '(unlabelled)'} · "
            f"support={cluster['support']} · scope={cluster['cause_scope']} · "
            f"probe={','.join(cluster.get('discrimination_profile') or []) or 'none'}"
        )
    # Aug A2 / standing constraint 2: an abstention rate nobody reads is not a
    # signal. Each reason names a different remedy, so report them separately
    # instead of one "did not cluster" total.
    by_reason: dict[str, int] = {}
    for entry in taxonomy["taxonomy"].get("abstained") or []:
        reason = str(entry.get("reason") or "unknown")
        by_reason[reason] = by_reason.get(reason, 0) + int(entry.get("support") or 0)
    for reason, support in sorted(by_reason.items()):
        typer.echo(f"  abstained · {reason} · {support} observations")
    if retired:
        typer.echo(
            f"{len(retired)} earlier taxonomy version(s) retired "
            "(string-keyed, migration 133); pinned receipts still resolve them."
        )

@app.command("correct-measurement")
def correct_measurement_command(
    source_practice_item_id: Annotated[
        str, typer.Argument(help="Attempted PracticeItem whose contract is being corrected.")
    ],
    corrected_item_path: Annotated[
        Path,
        typer.Argument(
            help="YAML containing corrected PracticeItem fields (include a new id to choose it)."
        ),
    ],
    reason: Annotated[
        str, typer.Option("--reason", help="Required audit reason for the correction.")
    ],
    projection_version: Annotated[
        str,
        typer.Option(
            "--projection-version",
            help="Exact projection version authorized to consume this correction.",
        ),
    ],
    reinterpret_history: Annotated[
        bool,
        typer.Option(
            "--reinterpret-history/--preserve-history",
            help="Let the named projection reinterpret old evidence when task invariants match.",
        ),
    ] = False,
    vault: Annotated[
        Path | None, typer.Option("--vault", help="Vault root.")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit the append-only correction receipt.")
    ] = False,
) -> None:
    """Supersede an attempted item without rewriting its historical file."""

    from learnloop.attempts.measurement_corrections import create_measurement_correction
    from learnloop.vault.yaml_io import read_yaml

    root = _root(vault)
    payload = read_yaml(corrected_item_path)
    corrected_id = str(payload.pop("id")) if payload.get("id") else None
    result = create_measurement_correction(
        root,
        _repository(root),
        source_practice_item_id=source_practice_item_id,
        corrected_fields=payload,
        corrected_practice_item_id=corrected_id,
        reason=reason,
        consuming_projection_version=projection_version,
        reinterpret_historical_evidence=reinterpret_history,
    )
    receipt = asdict(result)
    if json_output:
        typer.echo(_dump({"version": 1, **receipt}))
        return
    typer.echo(
        f"Created {result.corrected_practice_item_id}; "
        f"recorded {len(result.correction_ids)} correction edge(s) "
        f"for {result.consuming_projection_version}."
    )

@app.command("probe-families")
def probe_families_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    promote: Annotated[str | None, typer.Option("--promote", help="Promote family:version to trusted (gates must recommend it unless --force).")] = None,
    retire: Annotated[str | None, typer.Option("--retire", help="Retire family:version.")] = None,
    revise: Annotated[str | None, typer.Option("--revise", help="Create the next draft version of a family id.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Apply --promote even when the metric gates do not recommend it.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON overview.")] = False,
) -> None:
    """Family-version lifecycle (probe redesign §9.7, Checkpoint 4.7):
    metric-gated trusted/revise/retire transitions with a persisted audit trail.
    Without flags, prints every family version's status and recommendation."""

    from learnloop.diagnosis.probe_lifecycle import (
        LifecycleTransitionError,
        apply_family_lifecycle_transition,
        evaluate_family_lifecycle,
        family_lifecycle_overview,
        revise_family_version,
    )

    def parse_ref(ref: str) -> tuple[str, int]:
        family_id, _, version = ref.partition(":")
        if not family_id or not version.isdigit():
            raise typer.BadParameter(f"expected family:version, got {ref!r}")
        return family_id, int(version)

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)

    try:
        if promote is not None:
            family_id, version = parse_ref(promote)
            assessment = evaluate_family_lifecycle(loaded, repository, family_id, version)
            if assessment.recommendation != "promote_to_trusted" and not force:
                typer.echo(
                    f"Refusing to promote {family_id} v{version}: recommendation is "
                    f"{assessment.recommendation} ({'; '.join(assessment.reasons)}). Use --force to override."
                )
                raise typer.Exit(code=1)
            apply_family_lifecycle_transition(
                repository,
                family_id=family_id,
                version=version,
                to_status="trusted",
                reason={**assessment.as_dict(), "forced": force},
            )
            typer.echo(f"Promoted {family_id} v{version} to trusted.")
            return
        if retire is not None:
            family_id, version = parse_ref(retire)
            assessment = evaluate_family_lifecycle(loaded, repository, family_id, version)
            apply_family_lifecycle_transition(
                repository,
                family_id=family_id,
                version=version,
                to_status="retired",
                reason=assessment.as_dict(),
            )
            typer.echo(f"Retired {family_id} v{version}. Historical observations replay unchanged.")
            return
        if revise is not None:
            new_version = revise_family_version(repository, revise)
            typer.echo(f"Created {revise} v{new_version} as draft.")
            return
    except LifecycleTransitionError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    assessments = family_lifecycle_overview(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "families": [a.as_dict() for a in assessments]}))
        return
    if not assessments:
        typer.echo("No probe family versions stored.")
        return
    for assessment in assessments:
        metrics = assessment.metrics
        typer.echo(
            f"{assessment.family_id} v{assessment.version} [{assessment.status}] -> "
            f"{assessment.recommendation} "
            f"(real n={metrics.real_sample_size}, obs={metrics.eligible_observations}, "
            f"neg-info={metrics.negative_information_rate}, "
            f"regrade={metrics.regrade_agreement} over {metrics.regrade_checks})"
        )
        for reason in assessment.reasons:
            typer.echo(f"    {reason}")

@app.command("probe-gate")
def probe_gate_command(
    learning_object_id: Annotated[str, typer.Argument(help="Learning Object whose family/card bindings to gate.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    family: Annotated[str | None, typer.Option("--family", help="Only this family template id.")] = None,
    trials: Annotated[int, typer.Option("--trials", min=1, max=10, help="Planted trials per hypothesis.")] = 3,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON results.")] = False,
) -> None:
    """Run the §9.6 family admission gate with LLM planted-trial traces for one
    Learning Object's applicable family/card bindings. Outcomes are recorded
    under evidence_source='synthetic_gate' only — structural and simulation
    validity, never real-learner calibration."""

    from learnloop.diagnosis.probe_instance_generation import (
        applicable_families,
        run_llm_family_gate,
    )

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    learning_object = loaded.learning_objects.get(learning_object_id)
    if learning_object is None:
        typer.echo(f"Unknown Learning Object {learning_object_id}.")
        raise typer.Exit(code=1)
    resolved = ready_client_for_task(root, loaded.config, "authoring")
    provider_name, client = resolved.provider_name, resolved.client
    if client is None:
        typer.echo(f"AI provider {provider_name} is unavailable; the gate needs planted trials.")
        raise typer.Exit(code=1)

    results: list[dict[str, Any]] = []
    for template in applicable_families(loaded, learning_object, repository):
        if family is not None and template.id != family:
            continue
        gate = run_llm_family_gate(
            loaded, repository, learning_object_id, template, client, trials_per_hypothesis=trials
        )
        if gate is None:
            results.append({"family_template_id": template.id, "version": template.version, "ran": False})
            continue
        results.append(
            {
                "family_template_id": template.id,
                "version": template.version,
                "ran": True,
                "accepted": gate.accepted,
                "reasons": gate.reasons,
                "reverse_match_accuracy": gate.reverse_match_accuracy,
            }
        )
    if json_output:
        typer.echo(_dump({"version": 1, "learning_object_id": learning_object_id, "families": results}))
        return
    if not results:
        typer.echo("No applicable family templates for this Learning Object.")
        return
    for entry in results:
        if not entry["ran"]:
            typer.echo(f"{entry['family_template_id']} v{entry['version']}: skipped (cannot bind or no trials)")
            continue
        verdict = "ACCEPTED" if entry["accepted"] else "REJECTED"
        typer.echo(f"{entry['family_template_id']} v{entry['version']}: {verdict}")
        for slot, acc in sorted(entry["reverse_match_accuracy"].items()):
            typer.echo(f"    reverse-match {slot}: {acc:.2f}")
        for reason in entry["reasons"]:
            typer.echo(f"    {reason}")

__all__ = [name for name in globals() if not name.startswith("__")]
