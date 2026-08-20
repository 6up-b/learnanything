from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

ingest_batches_app = typer.Typer(no_args_is_help=True, help="Inspect and control durable ingest batches (§6.2).")

@ingest_batches_app.command("list")
def ingest_batches_list(
    limit: Annotated[int, typer.Option("--limit", help="Max batches to list.")] = 30,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    batch_rows = runner.repo.list_ingest_batches(limit=limit)
    jobs_by_batch = runner.repo.ingest_jobs_for_batches(
        batch["id"] for batch in batch_rows
    )
    batches = [
        _batch_json(
            runner,
            batch["id"],
            batch=batch,
            jobs=jobs_by_batch.get(batch["id"], []),
        )
        for batch in batch_rows
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "batches": batches}))
        return
    if not batches:
        typer.echo("No ingest batches.")
        return
    for batch in batches:
        done = sum(1 for job in batch["jobs"] if job["status"] == "completed")
        typer.echo(f"{batch['id']} [{batch['status']}] {batch['workflow_type']} {done}/{len(batch['jobs'])} jobs")

@ingest_batches_app.command("show")
def ingest_batches_show(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    batch = _batch_json(runner, batch_id)
    if not batch:
        typer.echo(_dump({"version": 1, "error": "ingest_batch_not_found"}) if json_output else f"Batch {batch_id} not found.", err=not json_output)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": batch}))
        return
    typer.echo(f"Batch {batch['id']} [{batch['status']}] {batch['workflow_type']}")
    for job in batch["jobs"]:
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<16} {job['status']:<12} phase={job.get('phase')}")

@ingest_batches_app.command("cancel")
def ingest_batches_cancel(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    if runner.repo.get_ingest_batch(batch_id) is None:
        typer.echo(f"Batch {batch_id} not found.", err=True)
        raise typer.Exit(code=1)
    runner.cancel_batch(batch_id)
    batch = _batch_json(runner, batch_id)
    typer.echo(_dump({"version": 1, "batch": batch}) if json_output else f"Batch {batch_id} [{batch['status']}]")

@ingest_batches_app.command("resume")
def ingest_batches_resume(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    if runner.repo.get_ingest_batch(batch_id) is None:
        typer.echo(f"Batch {batch_id} not found.", err=True)
        raise typer.Exit(code=1)
    runner.resume_batch(batch_id)
    runner.recover_stale_leases()
    runner.drain()
    batch = _batch_json(runner, batch_id)
    typer.echo(_dump({"version": 1, "batch": batch}) if json_output else f"Batch {batch_id} [{batch['status']}]")

__all__ = [name for name in globals() if not name.startswith("__")]
