"""The rich figure job type (``figure_rich``): one Show me animation written, checked, rendered and stored.

The durable host that runs it is :mod:`learnloop.content.pipeline.jobs`; what the type is (its handler and its
flags) is its row in :mod:`learnloop.content.pipeline.job_types`.
"""

from __future__ import annotations

from typing import Any

from learnloop.content.pipeline.runner import IngestRunnerError, JobCancelled, JobContext


def handle_figure_rich(ctx: JobContext) -> dict[str, Any]:
    """figure_rich (Reader RW5d P2b): write, check, render and store one rich
    figure (a Manim animation) from the figure author's brief.

    Payload: the rich job's (``learnloop.figures.rich``): the request, the
    quick figure it follows (or none), the input hash, the brief, what the
    author was sent and the input's spans. The figure service owns the row;
    a job that ends with no row (the switches or the opt-in changed, held-out
    material, the plan down) fails with its code, ``waiting_for_plan``
    retryable on a later read. Cancelled at the next ``report()``."""

    from learnloop import provenance
    from learnloop.db.stores.provenance import continue_job_trace
    from learnloop.figures.rich import RichJobStopped, run_rich_job
    from learnloop.vault.loader import load_vault

    # The ingest drain opens no trace scope per job, so this one is the job's
    # own and ends with it: continuing the press's trace on the drain thread
    # without it would leave that trace on every later job the thread runs.
    with provenance.trace_scope():
        continue_job_trace(ctx.repo, ctx.job_id)
        vault = load_vault(ctx.vault_root)
        factory = ctx.services.figure_rich_client_factory
        client = factory(ctx) if factory is not None else None
        ctx.report("writing", message="writing an animation for this passage")
        try:
            return run_rich_job(
                vault, ctx.repo, ctx.payload, client=client,
                report=lambda phase, message: ctx.report(phase, message=message),
                renderer=ctx.services.figure_rich_renderer, function_runner=ctx.services.figure_function_runner,
                cancellation=(JobCancelled,), clock=ctx.clock)
        except RichJobStopped as exc:
            raise IngestRunnerError(exc.message, code=exc.code, retryable=exc.retryable) from exc
