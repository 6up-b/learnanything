"""`learnloop ai`: provider sign-in, status, a latency check and a side-by-side comparison.

`learnloop ai signin chatgpt` is "Continue with ChatGPT" for the terminal: it
opens the system browser on OpenAI's sign-in page, listens on 127.0.0.1 for
the callback, and saves the validated sign-in outside every vault (the
LearnLoop config directory). Nothing here prints a token. `learnloop ai
compare` runs the same grading, diagnosis and generation on several
subscription profiles (Codex and the ChatGPT plan) on a vault copy
(``learnloop.cli.ai_compare``).
"""
from __future__ import annotations

from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
import statistics
import time
from typing import Annotated, Any
import webbrowser

import typer

from learnloop.cli.receipts import bind_command_vault
from learnloop.cli.render import _dump

ai_app = typer.Typer(no_args_is_help=True, help="AI provider sign-in, status and checks.")

PROVIDERS = ("chatgpt",)
#: The probe's prompt-side estimate (tokens); its output budget is the shared
#: policy's for each profile (``learnloop.ai.output_budget``: the profile's
#: ``max_tokens``, else ``ai.output_tokens``), so a reasoning model is never
#: cut off before it answers and the timing is the model's, not a truncation.
LATENCY_INPUT_TOKENS = 400


def _require_chatgpt(provider: str) -> None:
    if provider.strip().lower() != "chatgpt":
        raise typer.BadParameter(f"Unknown provider {provider!r}; supported: {', '.join(PROVIDERS)}.")


def _fail(message: str, *, json_output: bool, code: str = "error", **extra: Any) -> None:
    if json_output:
        typer.echo(_dump({"version": 1, "ok": False, "error": code, "message": message, **extra}))
    else:
        typer.echo(message, err=True)
    raise typer.Exit(code=1)


WELCOME = (
    "You're using your ChatGPT plan.\n"
    "AI requests that LearnLoop routes to a chatgpt_plan profile now use your ChatGPT plan. "
    "Manage usage in ChatGPT settings: https://chatgpt.com/settings/usage"
)


@ai_app.command("signin")
def ai_signin(
    provider: Annotated[str, typer.Argument(help="The provider to sign in to: chatgpt.")],
    new_account: Annotated[bool, typer.Option("--new-account", help="Register a new client (switch ChatGPT accounts).")] = False,
    consent: Annotated[bool, typer.Option("--consent", help="Ask for consent again, e.g. to enable ChatGPT plan usage after a decline.")] = False,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="Print the sign-in URL instead of opening a browser.")] = False,
    port: Annotated[int | None, typer.Option("--port", min=0, max=65535, help="Loopback callback port (default 1455, else any free port).")] = None,
    timeout: Annotated[float, typer.Option("--timeout", min=10, max=3600, help="Seconds to wait for the browser.")] = 300.0,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Continue with ChatGPT: sign in once per machine so `chatgpt_plan` profiles can use your plan.

    Your browser opens OpenAI's sign-in page. After you approve, it returns to
    LearnLoop on 127.0.0.1 and the sign-in is saved in the LearnLoop config
    directory (the OS keyring when one is usable, else a 0600 file), never in a
    vault. A later sign-in reuses the saved registration.
    """

    _require_chatgpt(provider)
    from learnloop.ai.chatgpt_plan.oauth import SignInError
    from learnloop.ai.chatgpt_plan.session import PlanSession
    from learnloop.ai.chatgpt_plan.store import StoreError

    session = PlanSession()
    try:
        pending = session.begin_sign_in(new_account=new_account, consent=consent, port=port)
    except (SignInError, StoreError) as exc:
        _fail(str(exc), json_output=json_output, code=getattr(exc, "code", "sign_in_failed"))
        return
    opened = False
    if not no_browser:
        try:
            opened = webbrowser.open(pending.authorize_url)
        except webbrowser.Error:
            opened = False
    stream_err = json_output
    if opened:
        typer.echo("Opened your browser to sign in with ChatGPT. Waiting for it to return…", err=stream_err)
    else:
        typer.echo("Open this URL in a browser on this machine to sign in with ChatGPT:", err=stream_err)
        typer.echo(pending.authorize_url, err=stream_err)
    try:
        result = pending.wait(timeout=timeout)
    except (SignInError, StoreError) as exc:
        _fail(str(exc), json_output=json_output, code=getattr(exc, "code", "sign_in_failed"))
        return
    except KeyboardInterrupt:
        pending.close()
        _fail("Sign-in cancelled.", json_output=json_output, code="cancelled")
        return
    payload = {"version": 1, "ok": True, **result.as_dict(), "store_dir": str(session.store.root)}
    if json_output:
        typer.echo(_dump(payload))
        return
    who = result.email or "your ChatGPT account"
    typer.echo(f"Signed in with ChatGPT as {who}.")
    if not result.plan_usage_enabled:
        typer.echo(
            "ChatGPT plan usage was not granted, so chatgpt_plan profiles stay unavailable. To enable it, run "
            "`learnloop ai signin chatgpt --consent` and allow plan usage, or route these tasks to another provider."
        )
        return
    if result.welcome_pending:
        typer.echo("")
        typer.echo(WELCOME)
        session.acknowledge_welcome()


@ai_app.command("signout")
def ai_signout(
    provider: Annotated[str, typer.Argument(help="chatgpt")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Sign out: revoke the renewable session, then clear the saved tokens on this machine."""

    _require_chatgpt(provider)
    from learnloop.ai.chatgpt_plan.session import PlanSession

    result = PlanSession().sign_out()
    if json_output:
        typer.echo(_dump({"version": 1, "ok": bool(result["signed_out"]), **result}))
    else:
        typer.echo(result["message"], err=not result["signed_out"])
    if not result["signed_out"]:
        raise typer.Exit(code=1)


@ai_app.command("resume")
def ai_resume(
    provider: Annotated[str, typer.Argument(help="chatgpt")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """End a usage-limit pause now, so the next request tries the ChatGPT plan again."""

    _require_chatgpt(provider)
    from learnloop.ai.chatgpt_plan.session import PlanSession

    session = PlanSession()
    session.resume()
    status = session.status().as_dict()
    if json_output:
        typer.echo(_dump({"version": 1, "ok": True, **status}))
    else:
        typer.echo(status["message"])


@ai_app.command("status")
def ai_status(
    provider: Annotated[str, typer.Argument(help="chatgpt")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Also list this vault's chatgpt_plan profiles and the routes that use them.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """This machine's ChatGPT sign-in and plan state, from local files only (no network)."""

    _require_chatgpt(provider)
    from learnloop.ai.chatgpt_plan.routes import plan_profiles
    from learnloop.ai.chatgpt_plan.session import PlanSession
    from learnloop.ai.routing import runtime_for_provider
    from learnloop.vault.loader import load_vault

    status = PlanSession().status()
    payload: dict[str, Any] = {"version": 1, **status.as_dict()}
    if vault is not None:
        loaded = load_vault(vault.resolve())
        profiles = plan_profiles(loaded.config)
        for entry in profiles:
            runtime = runtime_for_provider(loaded.root, loaded.config, entry["name"])
            entry["ready"] = runtime.ready
            entry["message"] = runtime.message
        payload["profiles"] = profiles
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(payload["message"])
    if status.signed_in:
        typer.echo(f"account: {status.email or status.subject} · client {status.client_id} · tokens in {status.secret_store}")
    if payload.get("paused_until"):
        typer.echo(f"paused until {payload['paused_until']} · manage usage: {payload['manage_usage_url']}")
    for entry in payload.get("profiles", []):
        uses = ", ".join(entry["routes"] + (["active_provider"] if entry["active_provider"] else [])
                         + (["fallback_provider"] if entry["fallback_provider"] else [])) or "no route"
        flag = "ready" if entry["ready"] else "not ready"
        typer.echo(f"profile {entry['name']} ({entry['model']}): {flag}; used by {uses}")


@ai_app.command("models")
def ai_models(
    provider: Annotated[str, typer.Argument(help="chatgpt")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Use a profile's base URL from this vault (with --profile).")] = None,
    profile: Annotated[str | None, typer.Option("--profile", help="A chatgpt_plan profile in --vault.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List the models your ChatGPT account offers (one unbilled request with your sign-in)."""

    _require_chatgpt(provider)
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.ai.providers.chatgpt_plan import list_plan_models
    from learnloop.config.schema import CHATGPT_PLAN_API_BASE_URL, CHATGPT_PLAN_PROFILE_TYPE
    from learnloop.vault.loader import load_vault

    base_url = CHATGPT_PLAN_API_BASE_URL
    if (vault is None) != (profile is None):
        _fail("--vault and --profile go together.", json_output=json_output)
    if vault is not None and profile is not None:
        configured = load_vault(vault.resolve()).config.ai.providers.get(profile)
        if configured is None or configured.type != CHATGPT_PLAN_PROFILE_TYPE:
            _fail(f"{profile!r} is not a chatgpt_plan profile in {vault}.", json_output=json_output)
        base_url = configured.base_url or CHATGPT_PLAN_API_BASE_URL
    try:
        models = list_plan_models(base_url)
    except AIProviderUnavailable as exc:
        _fail(str(exc), json_output=json_output, code=type(exc).__name__)
        return
    if json_output:
        typer.echo(_dump({"version": 1, "ok": True, "models": models}))
        return
    for model in models:
        typer.echo(f"{model['slug']}\t{model['display_name']}")
    if not models:
        typer.echo("No models are listed for this account.")


@ai_app.command("latency")
def ai_latency(
    vault: Annotated[Path, typer.Option("--vault", help="Vault whose provider profiles to compare (receipts land here; use a fixtures-local copy).")],
    provider: Annotated[list[str], typer.Option("--provider", help="A provider profile to time; repeatable (e.g. chatgpt and codex_low).")],
    runs: Annotated[int, typer.Option("--runs", min=1, max=20, help="Calls per provider.")] = 3,
    timeout: Annotated[float, typer.Option("--timeout", min=5, max=600, help="Seconds per call.")] = 120.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="USD per million tokens; required for a metered profile.")] = None,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="A reservation cap for every metered profile together: each call reserves its prompt plus its full output budget (never what is billed).")] = 0.50,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the plan; build no client and send nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Time a tiny structured call through each provider (wall clock per call).

    The prompt carries no vault or learner text. Subscription profiles (Codex,
    chatgpt_plan) estimate cost from reported usage; a metered profile needs
    --price-per-million, and all metered profiles together stay inside one
    --max-cost-usd (a plan whose combined estimate exceeds it is refused before
    any call). Each call asks for and reserves the profile's output budget
    under the shared policy; a truncated answer is logged and counted as a
    failed call (one physical request per timed call, no retry). Every call
    leaves a receipt in the vault.
    """

    from learnloop.ai.errors import AIOutputTruncated, AIProviderUnavailable
    from learnloop.ai.execution import generation_limit, single_request
    from learnloop.ai.output_budget import output_budget, record_truncation
    from learnloop.ai.routing import client_for_provider, route_profile_mismatch, runtime_for_provider
    from learnloop.ai.schemas import WireModel
    from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded, is_subscription_transport
    from learnloop.ai.transport import execute_structured_operation
    from learnloop.ai.usage import consume_client_usage
    from learnloop.vault.loader import load_vault

    class LatencyProbe(WireModel):
        ok: bool
        n: int

    loaded = load_vault(vault.resolve())
    bind_command_vault(loaded.root)
    config = loaded.config
    names = list(dict.fromkeys(provider))

    def call_usd(tokens: int) -> float | None:
        # The same per-call figure every metered request reserves below.
        return tokens * price_per_million / 1_000_000 if price_per_million is not None else None

    plan = []
    for name in names:
        profile = config.ai.providers.get(name)
        if profile is None:
            _fail(f"No provider profile named {name!r} in {loaded.root / 'learnloop.toml'}.", json_output=json_output)
        mismatch = route_profile_mismatch(config, name, None)
        if mismatch:
            _fail(mismatch, json_output=json_output)
        subscription = is_subscription_transport(profile=profile)
        if not subscription and price_per_million is None:
            _fail(f"{name!r} is metered ({profile.type}); pass --price-per-million to bound its cost.",
                  json_output=json_output, code="unknown_price")
        budget_tokens = output_budget(config, None, provider=name)
        tokens_per_call = LATENCY_INPUT_TOKENS + budget_tokens
        per_call_usd = call_usd(tokens_per_call)
        plan.append({
            "provider": name, "type": profile.type, "model": profile.model,
            "billing": "subscription" if subscription else "metered", "calls": runs,
            "output_tokens": budget_tokens, "tokens_per_call": tokens_per_call,
            "estimated_tokens": runs * tokens_per_call,
            "estimated_usd": float(Decimal(str(per_call_usd)) * runs) if per_call_usd is not None else None,
        })
    # One dollar cap for every metered provider together; subscription
    # profiles keep their own (estimate-only) accounting per provider.
    metered = [entry for entry in plan if entry["billing"] == "metered"]
    # Decimal, like SpendBudget: the plan admits exactly what the per-call
    # reservations below will admit (a float sum can overshoot an exact cap).
    metered_usd = (float(sum((Decimal(str(call_usd(entry["tokens_per_call"]))) * runs for entry in metered),
                             Decimal(0))) if metered else 0)
    metered_tokens = sum(runs * entry["tokens_per_call"] for entry in metered)
    metered_budget = SpendBudget(SpendCaps(
        max_candidates=0, max_pairs=0, max_retries=0, max_calls=runs * len(metered),
        max_total_tokens=metered_tokens * 4, max_estimated_usd=max_cost_usd,
    )) if metered else None
    reason = None
    if metered_budget is not None:
        try:
            metered_budget.check(SpendEstimate(calls=runs * len(metered), total_tokens=metered_tokens,
                                               estimated_usd=metered_usd))
        except SpendLimitExceeded as exc:
            reason = (f"The metered providers together estimate ${metered_usd:.4f}, over --max-cost-usd "
                      f"${max_cost_usd:g} ({exc}). Lower --runs, drop a provider or raise the cap.")
    if dry_run:
        payload = {"version": 1, "dry_run": True, "plan": plan, "admissible": reason is None, "reason": reason,
                   "metered_estimated_usd": metered_usd, "max_cost_usd": max_cost_usd}
        if json_output:
            typer.echo(_dump(payload))
        else:
            for entry in plan:
                typer.echo(f"{entry['provider']} ({entry['type']}, {entry['model']}, {entry['billing']}): "
                           f"{entry['calls']} calls, ~{entry['estimated_tokens']} tokens")
            if metered:
                typer.echo(f"metered total: ~${metered_usd:.4f} of ${max_cost_usd:g}")
            if reason:
                typer.echo(reason, err=True)
        if reason:
            raise typer.Exit(code=1)
        return
    if reason:
        _fail(reason, json_output=json_output, code="over_budget", metered_estimated_usd=metered_usd,
              max_cost_usd=max_cost_usd)

    results = []
    for entry in plan:
        name = entry["provider"]
        subscription = entry["billing"] == "subscription"
        runtime = runtime_for_provider(loaded.root, config, name)
        row: dict[str, Any] = {**entry, "ready": runtime.ready, "runs": []}
        results.append(row)
        if not runtime.ready:
            row["error"] = runtime.message
            continue
        try:
            client = client_for_provider(loaded.root, config, name)
        except AIProviderUnavailable as exc:
            row["error"] = str(exc)
            continue
        tokens_per_call = entry["tokens_per_call"]
        if subscription or metered_budget is None:
            budget = SpendBudget(SpendCaps(max_candidates=0, max_pairs=0, max_retries=0, max_calls=runs,
                                           max_total_tokens=runs * tokens_per_call * 4, max_estimated_usd=max_cost_usd),
                                 subscription=subscription)
        else:
            budget = metered_budget  # shared: every metered provider draws on one --max-cost-usd
        before = budget.used
        for index in range(1, runs + 1):
            prompt = (f"LearnLoop latency probe {index}. Return the JSON object "
                      f'{{"ok": true, "n": {index}}} and nothing else.')
            estimate = SpendEstimate(calls=1, total_tokens=tokens_per_call, estimated_usd=call_usd(tokens_per_call))
            run: dict[str, Any] = {"n": index}
            try:
                with budget.request(estimate) as charge:
                    started = time.perf_counter()
                    try:
                        with (nullcontext() if subscription else single_request()), \
                                generation_limit(entry["output_tokens"]):
                            answer = execute_structured_operation(
                                client, purpose="ai_latency_probe", prompt=prompt, result_model=LatencyProbe,
                                timeout_seconds=timeout,
                            )
                        run["ok"] = bool(answer.ok) and answer.n == index
                    except AIOutputTruncated as exc:
                        # Never accepted; logged. A timed call is one physical
                        # request, so it is not retried: the call failed.
                        run["ok"] = False
                        run["error"] = f"{type(exc).__name__}: {exc}"
                        run["truncation"] = record_truncation(
                            role="ai_latency_probe", provider=name, model=entry["model"],
                            budget=entry["output_tokens"], retry_budget=None)
                    except AIProviderUnavailable as exc:
                        run["ok"] = False
                        run["error"] = f"{type(exc).__name__}: {exc}"
                    run["seconds"] = round(time.perf_counter() - started, 3)
                    usage = consume_client_usage(client)
                    run["input_tokens"], run["output_tokens"] = usage.input_tokens, usage.output_tokens
                    timing = getattr(client, "last_timing", None)
                    if isinstance(timing, dict):
                        run["seconds_to_first_event"] = (round(timing["first_event"], 3)
                                                         if timing.get("first_event") is not None else None)
                    reported = usage.total_tokens or None
                    charge.reconcile(total_tokens=reported, estimated_usd=(
                        reported * price_per_million / 1_000_000 if reported and price_per_million is not None else None))
            except SpendLimitExceeded as exc:
                row["error"] = f"stopped by the spend caps: {exc}"
                break
            row["runs"].append(run)
        times = [run["seconds"] for run in row["runs"] if run.get("ok")]
        row["ok_calls"] = len(times)
        row["seconds"] = ({"min": min(times), "median": round(statistics.median(times), 3), "max": max(times)}
                          if times else None)
        after = budget.used
        row["charged"] = {
            "calls": after.calls - before.calls, "total_tokens": after.total_tokens - before.total_tokens,
            "estimated_usd": (after.estimated_usd - before.estimated_usd
                              if after.estimated_usd is not None and before.estimated_usd is not None else None),
        }
    payload = {"version": 1, "dry_run": False, "results": results}
    if metered_budget is not None:
        payload["metered_charged_usd"] = metered_budget.used.estimated_usd
        payload["max_cost_usd"] = max_cost_usd
    if json_output:
        typer.echo(_dump(payload))
        return
    for row in results:
        if row.get("seconds"):
            seconds = row["seconds"]
            typer.echo(f"{row['provider']} ({row['type']}, {row['model']}): median {seconds['median']}s "
                       f"(min {seconds['min']}s, max {seconds['max']}s) over {row['ok_calls']}/{len(row['runs'])} calls")
        else:
            typer.echo(f"{row['provider']} ({row['type']}): no successful call. {row.get('error') or ''}".rstrip())
        for run in row["runs"]:
            if not run.get("ok"):
                typer.echo(f"  call {run['n']}: {run.get('error') or 'unexpected answer'}")


@ai_app.command("compare")
def ai_compare(
    vault: Annotated[Path, typer.Option("--vault", help="A backup-API copy of a vault (receipts land here); with --copy-from, the new copy's directory.")],
    profiles: Annotated[list[str], typer.Option("--profiles", help="Subscription profiles to compare, comma-separated or repeated (e.g. codex,chatgpt).")],
    copy_from: Annotated[Path | None, typer.Option("--copy-from", help="Copy this vault to --vault first (backup API; also with --dry-run); the original is only read.")] = None,
    attempts: Annotated[int, typer.Option("--attempts", min=0, max=20, help="Attempts to blind-grade per profile (latest non-pass and pass first).")] = 3,
    attempt_id: Annotated[list[str] | None, typer.Option("--attempt", help="An attempt to grade (repeatable; replaces the automatic choice).")] = None,
    diagnosis_attempt: Annotated[str | None, typer.Option("--diagnosis-attempt", help="The attempt to diagnose (default: the latest non-pass that needs one).")] = None,
    diagnosis_mode: Annotated[str, typer.Option("--diagnosis-mode", help="History mode of the diagnosis: snapshot (default), full or exact.")] = "snapshot",
    no_diagnosis: Annotated[bool, typer.Option("--no-diagnosis", help="Skip the diagnosis.")] = False,
    no_generation: Annotated[bool, typer.Option("--no-generation", help="Skip the structured generation.")] = False,
    timeout: Annotated[int, typer.Option("--timeout", min=30, max=3600, help="Seconds per call (a workspace turn's rounds included).")] = 900,
    output: Annotated[Path, typer.Option("--output", help="Directory for the JSON report (outside the vault).")] = Path("fixtures-local/reports/ai-compare"),
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the plan; build no client and send nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run the same grading, diagnosis and generation on each profile and compare them.

    For deciding whether a route moves from Codex to the ChatGPT plan: a few
    attempts blind-graded, one snapshot diagnosis (the plan's read-only
    workspace is served by LearnLoop and recorded exactly) and one teach-back
    authoring draft, per profile. The report holds ids, numbers and local
    explanations only (a failure as its code, never the provider's message):
    agreement, structured-output validity, latency, tokens per call, spend
    (estimated_only) and plan allowance (pause state, usage-limit errors).
    The vault gets model-call receipts and the comparison's own verdicts in
    its judgment ledger (never evidence). Subscription profiles only; a vault
    whose database git tracks (a working vault) or lies outside it is refused:
    pass --copy-from, which also copies a relocated database.
    """

    from datetime import datetime, timezone
    import json

    from learnloop.ai.errors import AIInterrupted
    from learnloop.cli.ai_compare import (
        CompareRefused,
        CompareRequest,
        copy_vault,
        database_location_reason,
        plan_compare,
        run_compare,
        tracked_database_reason,
    )
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import open_vault_repository

    names = tuple(dict.fromkeys(part.strip() for value in profiles for part in value.split(",") if part.strip()))
    request = CompareRequest(
        profiles=names, grading_attempts=attempts, attempt_ids=tuple(attempt_id or ()),
        diagnosis=not no_diagnosis, diagnosis_attempt_id=diagnosis_attempt, diagnosis_mode=diagnosis_mode,
        generation=not no_generation, timeout_seconds=timeout,
    )
    copied: list[str] = []
    try:
        if copy_from is not None:
            # A local copy sends nothing, so a dry run makes it too; run live on --vault next.
            copied = [str(path) for path in copy_vault(copy_from, vault)]
        loaded = load_vault(vault.resolve())
        # Both before the database is opened (which migrates it).
        reason = database_location_reason(loaded)
        if reason is not None:
            raise CompareRefused(reason, code="database_outside_vault")
        reason = tracked_database_reason(loaded, fresh_copy=copy_from is not None)
        if reason is not None:
            raise CompareRefused(reason, code="working_vault")
        bind_command_vault(loaded.root)
        repository = open_vault_repository(loaded.root, VaultPaths(loaded.root, loaded.config).sqlite_path)
        if dry_run:
            plan = plan_compare(loaded, repository, request)
            payload = {"version": 1, "dry_run": True, "vault": str(loaded.root), "copied": copied, **plan}
            if json_output:
                typer.echo(_dump(payload))
                return
            for row in plan["profiles"]:
                flag = "ready" if row["ready"] else f"not ready: {row['message']}"
                workspace = "workspace" if row["read_only_workspace"] else "no workspace"
                typer.echo(f"{row['provider']} ({row['type']}, {row['model']}, {workspace}): {flag}")
            targets = plan["targets"]
            typer.echo(f"grading: {', '.join(targets['grading']) or '-'}")
            typer.echo(f"diagnosis ({plan['diagnosis_mode']}): {targets['diagnosis'] or '-'}")
            typer.echo(f"generation (teach-back authoring): {targets['generation_item'] or '-'}")
            typer.echo(f"{plan['calls_per_profile']} calls per profile, {plan['max_calls']} at most")
            typer.echo("estimate (subscription: estimated_only, no dollar cost, no physical-request bound):")
            for name, estimate in plan["estimate"]["profiles"].items():
                typer.echo(
                    f"  {name}: {estimate['calls']} calls, ~{estimate['estimated_total_tokens']} tokens "
                    f"(input ~{estimate['estimated_input_tokens']}"
                    + (f", snapshot export ~{estimate['estimated_workspace_tokens']}"
                       if estimate["estimated_workspace_tokens"] else "")
                    + f", output up to {estimate['estimated_output_tokens']})")
                for planned in estimate["planned"]:
                    typer.echo(f"    {planned['kind']} {planned['target']}: ~{planned['total_tokens']} tokens")
            for note in targets["notes"]:
                typer.echo(f"note: {note}")
            if copied:
                typer.echo(f"copied to {loaded.root}; run without --copy-from and --dry-run to compare live")
            return
        report = run_compare(loaded, repository, request,
                             progress=None if json_output else (lambda message: typer.echo(message, err=True)))
    except CompareRefused as exc:
        _fail(str(exc), json_output=json_output, code=exc.code)
        return
    except AIInterrupted:
        _fail("Comparison interrupted.", json_output=json_output, code="interrupted")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=True)
    # Named after the run (its judgments' compare_run_id): two runs in one
    # second never share a file, and "x" never overwrites an earlier report.
    path = output / f"{stamp}-{report['run_id']}.json"
    payload = {"version": 1, "dry_run": False, "vault": str(loaded.root), "copied": copied, **report}
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    if json_output:
        typer.echo(_dump({**payload, "report_path": str(path)}))
        return
    for row in report["results"]:
        summary = row.get("summary")
        if not summary:
            hint = (row.get("failure") or {}).get("hint")
            typer.echo(f"{row['provider']}: {row.get('error') or 'not run'}" + (f": {hint}" if hint else ""))
            continue
        typer.echo(
            f"{row['provider']} ({row['model']}): {summary['valid']}/{summary['calls']} valid, median "
            f"{summary['seconds_median']}s, {summary['tokens_per_call']} tokens/call, "
            f"{summary['physical_requests']} requests"
            + (f", errors {', '.join(summary['errors'])}" if summary["errors"] else "")
            + (f"; stopped: {row['stopped']}" if row.get("stopped") else "")
        )
        failures = [(label, call) for label, call in [
            *((f"grading {attempt}", call) for attempt, call in (row.get("grading") or {}).items()),
            ("diagnosis", row.get("diagnosis")), ("generation", row.get("generation"))]
            if call and call.get("error")]
        for label, call in failures:
            failure = call.get("failure") or {}
            codes = ", ".join(str(failure[key]) for key in ("code", "http_status", "param") if failure.get(key))
            typer.echo(f"  {label}: {call['error']}" + (f" ({codes})" if codes else "")
                       + (f": {call['rejection']}" if call.get("rejection") else "")
                       + (f": {failure['hint']}" if failure.get("hint") else ""))
        spend = row.get("spend") or {}
        if spend:
            typer.echo(f"  spend: {spend['used']['calls']} calls, {spend['reported_total_tokens']} tokens reported "
                       f"(estimated_only; planned ~{spend['estimated_total_tokens']})")
        if row.get("allowance_after"):
            typer.echo(f"  plan allowance: {row['allowance_after']['state']}"
                       + (f", paused until {row['allowance_after']['paused_until']}"
                          if row["allowance_after"].get("paused_until") else ""))
    for pair in report["agreement"]:
        grading = pair["grading"]
        line = (f"{' vs '.join(pair['profiles'])}: grading {grading['compared']} compared, exact "
                f"{grading['exact_rate']}, criteria {grading['criterion_agreement']}")
        if pair.get("diagnosis"):
            diagnosis = pair["diagnosis"]
            line += (f"; diagnosis same classes {diagnosis['same_causal_classes']}, cited-attempt overlap "
                     f"{diagnosis['evidence_jaccard']}")
        if pair.get("generation"):
            line += f"; generation both valid {pair['generation']['both_valid']}"
        typer.echo(line)
    typer.echo(f"report: {path}")


__all__ = ["ai_app"]
