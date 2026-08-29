from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

depth_app = typer.Typer(
    no_args_is_help=True,
    help="Depth-edge authoring: owner-curated templates, LLM edge instances, deterministic admission, pinning (spec v2 depth).",
)

@depth_app.command("template-add")
def depth_template_add(
    slug: Annotated[str, typer.Argument(help="Stable template slug (snake case).")],
    body_file: Annotated[Path, typer.Argument(help="JSON template body: step_deltas, exit_gate_kind, fresh_proof_kind, eligible_pattern_slugs, optional capability_transitions.")],
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Create a depth-edge template (version 1, status draft)."""

    from learnloop.curriculum.depth_edge_authoring import DepthEdgeAuthoringError, create_edge_template

    repo = _repository(_root(vault))
    try:
        template_id, version_id = create_edge_template(
            repo, template_slug=slug, body=jsonlib.loads(body_file.read_text(encoding="utf-8"))
        )
    except DepthEdgeAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_dump({"version": 1, "template_id": template_id, "template_version_id": version_id}))

@depth_app.command("template-review")
def depth_template_review(
    version_id: Annotated[str, typer.Argument(help="Template version id.")],
    status: Annotated[str, typer.Option("--status", help="reviewed|retired")] = "reviewed",
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Mark a template version reviewed (only reviewed versions parent instances)."""

    from learnloop.curriculum.depth_edge_authoring import DepthEdgeAuthoringError, review_edge_template

    repo = _repository(_root(vault))
    try:
        review_edge_template(repo, version_id=version_id, status=status)
    except DepthEdgeAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_dump({"version": 1, "template_version_id": version_id, "status": status}))

@depth_app.command("templates")
def depth_templates_list(
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """List depth-edge templates and their versions."""

    repo = _repository(_root(vault))
    rows = []
    for template in repo.depth_edge_templates():
        versions = repo.depth_edge_template_versions_for(template["id"])
        rows.append({**template, "versions": versions})
    typer.echo(_dump({"version": 1, "templates": rows}))

@depth_app.command("edges-author")
def depth_edges_author(
    commitment_id: Annotated[str, typer.Argument(help="Commitment id.")],
    template_version_ids: Annotated[list[str], typer.Option("--template-version", help="Reviewed template version id (repeatable).")],
    count: Annotated[int, typer.Option("--count")] = 1,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """LLM-author edge instances from reviewed templates; each is gated and
    stored admitted/rejected with its admission report. Never activates."""

    from learnloop.curriculum.depth_edge_authoring import DepthEdgeAuthoringError, author_edge_instances

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    _provider_name, runtime, client = _ready_provider_for_task(
        vault_root, loaded.config, "authoring"
    )
    if client is None:
        typer.echo(runtime.message or "AI provider is unavailable.", err=True)
        raise typer.Exit(code=1)
    repo = _repository(vault_root)
    try:
        stored = author_edge_instances(
            repo, client, commitment_id=commitment_id,
            template_version_ids=list(template_version_ids), count=count,
        )
    except DepthEdgeAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_dump({"version": 1, "instances": stored}))

@depth_app.command("edges")
def depth_edges_list(
    commitment_id: Annotated[str, typer.Argument(help="Commitment id.")],
    status: Annotated[str | None, typer.Option("--status", help="proposed|admitted|rejected|confirmed|pinned")] = None,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """List edge instances (with admission reports) for one commitment."""

    repo = _repository(_root(vault))
    typer.echo(_dump({
        "version": 1,
        "instances": repo.depth_edge_instances_for(commitment_id, status=status),
    }))

@depth_app.command("backfill-rungs")
def depth_backfill_rungs(
    subject: Annotated[str | None, typer.Option("--subject", help="Limit to one subject id.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Report classifications without writing.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """LLM-classify legacy items into capability + task_features (deterministic
    validators admit each entry) and stamp the vault YAML in place. Annotation
    only — content, rubrics, evidence, and scheduling state are untouched."""

    from learnloop.curriculum.rung_backfill import RungBackfillError, backfill_item_rungs

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    _provider_name, runtime, client = _ready_provider_for_task(
        vault_root, loaded.config, "authoring"
    )
    if client is None:
        typer.echo(runtime.message or "AI provider is unavailable.", err=True)
        raise typer.Exit(code=1)
    repo = _repository(vault_root)
    try:
        report = backfill_item_rungs(vault_root, repo, client, subject=subject, dry_run=dry_run)
    except RungBackfillError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_dump({"version": 1, "dry_run": dry_run, **report}))

@depth_app.command("edges-confirm")
def depth_edges_confirm(
    commitment_id: Annotated[str, typer.Argument(help="Commitment id.")],
    instance_ids: Annotated[list[str], typer.Option("--instance", help="Admitted instance id (repeatable).")],
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Confirm admitted instances and PIN them into a new immutable envelope
    version + milestone rows. Auto-activation stays gated (U-018)."""

    from learnloop.curriculum.depth_edge_authoring import DepthEdgeAuthoringError, pin_admitted_edges

    repo = _repository(_root(vault))
    try:
        envelope_version_id = pin_admitted_edges(
            repo, commitment_id=commitment_id, instance_ids=list(instance_ids)
        )
    except DepthEdgeAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_dump({"version": 1, "envelope_version_id": envelope_version_id}))

__all__ = [name for name in globals() if not name.startswith("__")]
