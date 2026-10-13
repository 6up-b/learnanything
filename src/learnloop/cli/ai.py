"""`learnloop ai`: provider sign-in, status and a latency check.

`learnloop ai signin chatgpt` is "Continue with ChatGPT" for the terminal: it
opens the system browser on OpenAI's sign-in page, listens on 127.0.0.1 for
the callback, and saves the validated sign-in outside every vault (the
LearnLoop config directory). Nothing here prints a token.
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
LATENCY_OUTPUT_TOKENS = 64


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
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 0.05,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the plan; build no client and send nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Time a tiny structured call through each provider (wall clock per call).

    The prompt carries no vault or learner text. Subscription profiles (Codex,
    chatgpt_plan) estimate cost from reported usage; a metered profile needs
    --price-per-million, and all metered profiles together stay inside one
    --max-cost-usd (a plan whose combined estimate exceeds it is refused before
    any call). Every call leaves a receipt in the vault.
    """

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.ai.execution import generation_limit, single_request
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
    tokens_per_call = 400 + LATENCY_OUTPUT_TOKENS
    # The same per-call figure every metered request reserves below.
    call_usd = tokens_per_call * price_per_million / 1_000_000 if price_per_million is not None else None
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
        plan.append({
            "provider": name, "type": profile.type, "model": profile.model,
            "billing": "subscription" if subscription else "metered", "calls": runs,
            "estimated_tokens": runs * tokens_per_call,
            "estimated_usd": float(Decimal(str(call_usd)) * runs) if call_usd is not None else None,
        })
    # One dollar cap for every metered provider together; subscription
    # profiles keep their own (estimate-only) accounting per provider.
    metered = [entry for entry in plan if entry["billing"] == "metered"]
    # Decimal, like SpendBudget: the plan admits exactly what the per-call
    # reservations below will admit (a float sum can overshoot an exact cap).
    metered_usd = float(Decimal(str(call_usd)) * runs * len(metered)) if metered else 0
    metered_budget = SpendBudget(SpendCaps(
        max_candidates=0, max_pairs=0, max_retries=0, max_calls=runs * len(metered),
        max_total_tokens=runs * tokens_per_call * 4 * len(metered), max_estimated_usd=max_cost_usd,
    )) if metered else None
    reason = None
    if metered_budget is not None:
        try:
            metered_budget.check(SpendEstimate(calls=runs * len(metered), total_tokens=runs * tokens_per_call * len(metered),
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
            estimate = SpendEstimate(calls=1, total_tokens=tokens_per_call, estimated_usd=call_usd)
            run: dict[str, Any] = {"n": index}
            try:
                with budget.request(estimate) as charge:
                    started = time.perf_counter()
                    try:
                        with (nullcontext() if subscription else single_request()), generation_limit(LATENCY_OUTPUT_TOKENS):
                            answer = execute_structured_operation(
                                client, purpose="ai_latency_probe", prompt=prompt, result_model=LatencyProbe,
                                timeout_seconds=timeout,
                            )
                        run["ok"] = bool(answer.ok) and answer.n == index
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


__all__ = ["ai_app"]
