"""`learnloop experiments`: research experiments on vault copies (never production).

`experiments e0 prepare` makes backup-API copies of vaults under a
`fixtures-local` directory (never `arxiv_v2`). `experiments e0 run --dry-run`
plans E0 on those copies with zero network calls and no writes to them: the
frozen plan, the estimate against the $25 cap, and which keys are present
(names only). A run without `--dry-run` is the paid run: it needs
`--i-am-authorized-to-spend` (an orchestrator step after review) and a dry
run that fits. `experiments e0 report` renders the aggregate report.

The experiment package is imported only inside these commands.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

experiments_app = typer.Typer(no_args_is_help=True,
                              help="Research experiments on vault copies (never production serving).")
e0_app = typer.Typer(no_args_is_help=True, help="E0: hosted contextual source embeddings, no GPU (spec §5).")
experiments_app.add_typer(e0_app, name="e0")

_DEFAULT_ROOT = Path("fixtures-local") / "contextual-embeddings"


def _fail(exc: Exception) -> None:
    """Print a failure's SAFE message only (never a provider's text, which can
    echo a credential: fix round 4, High 8) and exit 1, unchained."""

    from learnloop.experiments.contextual_embeddings.boundary import safe_message

    typer.echo(json.dumps({"status": "invalid", "reason": safe_message(exc)}, sort_keys=True))
    raise typer.Exit(code=1) from None


@e0_app.command("prepare")
def e0_prepare(
    source: Annotated[list[Path], typer.Option("--from", help="A vault root to copy (repeatable; never arxiv_v2).")],
    label: Annotated[str, typer.Option("--label", help="Suffix of each copy's directory, such as a date.")],
    dest: Annotated[Path, typer.Option("--dest", help="Under a fixtures-local directory.")] = _DEFAULT_ROOT / "vaults",
) -> None:
    """Copy vaults through SQLite's backup API (WAL state included) for E0."""

    from learnloop.experiments.contextual_embeddings.corpus import prepare_copies

    try:
        copies = prepare_copies(source, dest, label=label)
    except (ValueError, OSError) as exc:
        _fail(exc)
    typer.echo(json.dumps({"status": "ok", "copies": copies}, sort_keys=True, indent=2))


@e0_app.command("run")
def e0_run(
    copy: Annotated[list[Path], typer.Option("--copy", help="A prepared vault copy (repeatable).")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: no network, nothing written to the copies.")] = False,
    env_file: Annotated[list[Path] | None, typer.Option(
        "--env-file", help="Load only the named key variables from this dotenv file (repeatable; never printed; a "
                           "variable with different values in two files is refused).")] = None,
    preflight_only: Annotated[bool, typer.Option(
        "--preflight-only", help="Load the env files and report the paid run's checks (keys present/absent only); "
                                 "no network, nothing spent.")] = False,
    perplexity_key_env: Annotated[str, typer.Option("--perplexity-key-env")] = "PERPLEXITY_API_KEY",
    voyage_key_env: Annotated[str, typer.Option("--voyage-key-env")] = "VOYAGE_API_KEY",
    openrouter_key_env: Annotated[str, typer.Option("--openrouter-key-env")] = "OPENROUTER_API_KEY",
    anthropic_key_env: Annotated[str, typer.Option(
        "--anthropic-key-env", help="The Messages API key variable (loaded only through --env-file).")] = "ANTHROPIC_API_KEY",
    reserve_share: Annotated[float, typer.Option(
        "--reserve-share", min=0.0, max=1.0, help="Source families reserved before question writing.")] = 0.0,
    out: Annotated[Path | None, typer.Option("--out", help="Write the plan (JSON) here.")] = None,
    markdown: Annotated[Path | None, typer.Option("--markdown", help="Write the plan (Markdown) here.")] = None,
    run_dir: Annotated[Path, typer.Option("--run-dir", help="The paid run's private directory.")] = _DEFAULT_ROOT / "runs",
    authorized: Annotated[bool, typer.Option(
        "--i-am-authorized-to-spend", help="The orchestrator's explicit authorization for the paid run.")] = False,
    reader_latency_budget_s: Annotated[float | None, typer.Option(
        "--reader-latency-budget-s", min=0.1,
        help="The pinned Reader p95 answer budget for S2/S4 (unset: those rules fail closed).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    new_authorization: Annotated[str | None, typer.Option(
        "--new-authorization",
        help="The orchestrator's reason for a new plan's budget while another plan's ledger exists (that "
             "ledger is sealed and its spend carried: the cap is cumulative).")] = None,
    reuse_run: Annotated[str | None, typer.Option(
        "--reuse-run",
        help="An earlier run id under --run-dir whose content-keyed stores this plan reuses (checkpoints, "
             "vectors, service copies, records); its ledger prices the remaining work.")] = None,
) -> None:
    """Plan (--dry-run), check (--preflight-only) or run E0 on prepared copies within the $40 cap."""

    from learnloop.experiments.contextual_embeddings.runner import dry_run as plan_dry_run, render_markdown

    key_envs = {"perplexity": perplexity_key_env, "voyage": voyage_key_env, "openrouter": openrouter_key_env,
                "anthropic": anthropic_key_env}
    try:
        from learnloop.experiments.contextual_embeddings.runner import require_paid_authorization

        if preflight_only:
            from learnloop.experiments.contextual_embeddings.runner import preflight

            report = preflight(copy, key_envs=key_envs, env_file=env_file or [], reserve_share=reserve_share,
                               reuse_run=reuse_run)
            typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2, default=str))
            if not report["ready"]:
                raise typer.Exit(code=1)
            return
        if not dry_run and not authorized:
            require_paid_authorization(authorized=False, dry_run_ok=False)
        plan = plan_dry_run(copy, key_envs=key_envs, env_file=env_file or [], reserve_share=reserve_share,
                            reuse_run=reuse_run)
        if out is not None:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(plan, sort_keys=True, indent=1, default=str) + "\n", encoding="utf-8")
        if markdown is not None:
            markdown.parent.mkdir(parents=True, exist_ok=True)
            markdown.write_text(render_markdown(plan), encoding="utf-8")
        if not dry_run:
            from learnloop.cli.receipts import bind_command_repository
            from learnloop.experiments.contextual_embeddings.boundary import require_codex_lockdown
            from learnloop.experiments.contextual_embeddings.live import run_live

            # Every E0 Codex turn must be the locked-down one (security lockdown 55063be64).
            require_codex_lockdown()
            # The estimate must fit what is left of the CUMULATIVE cap (relabel round).
            budget = plan.get("budget") or {"fits": plan["totals"]["fits_cap"]}
            require_paid_authorization(authorized=authorized, dry_run_ok=bool(budget["fits"]),
                                       unverified_prices=plan.get("prices", {}).get("unverified"))
            # Receipts go to each copy's experiment repository, never to a vault
            # found from the working directory (Codex review F4).
            result = run_live(copy, plan=plan, run_dir=run_dir, key_envs=key_envs,
                              reader_latency_budget_s=reader_latency_budget_s,
                              bind_receipts=bind_command_repository, new_authorization=new_authorization,
                              reuse_run=reuse_run)
            typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
            return
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001 - every failure prints its safe message only (High 8)
        _fail(exc)
    if json_output:
        typer.echo(json.dumps(plan, sort_keys=True, default=str))
    else:
        typer.echo(render_markdown(plan))


@e0_app.command("report")
def e0_report(
    results: Annotated[Path, typer.Option("--results", help="A results JSON written by the paid run.")],
    out: Annotated[Path | None, typer.Option("--out", help="Write the Markdown report here.")] = None,
) -> None:
    """Render the aggregate E0 report (refuses private fields)."""

    from learnloop.experiments.contextual_embeddings.report import render

    try:
        text = render(json.loads(results.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        _fail(exc)
    if out is not None:
        out.write_text(text, encoding="utf-8")
    typer.echo(text)
