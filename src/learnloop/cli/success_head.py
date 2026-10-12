"""`learnloop eval success-head`: the T8 replay report (offline research only).

Read-only over one snapshot of a vault copy. The embedding arms read vectors
already stored by `learnloop embeddings backfill`; the zero-data LLM arm reads
a cache outside the vault, filled only by the explicit, spend-capped
`--prepare-llm` step. Reports are aggregates; nothing is activated.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import math
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendCaps, SpendEstimate, is_subscription_transport
from learnloop.cli.field import _LEGACY_FALLBACK_HELP, _emit, _load_offline, _replay_inputs
from learnloop.cli.field_llm import METERED_ROUTE_TYPES, ProbabilityResult
from learnloop.db.connection import connect
from learnloop.vault.paths import VaultPaths


def _load(vault: Path, *, paid: bool):
    """Replay and dry runs read only the vault TOML; a paid step loads like
    `learnloop embeddings backfill`, so the app reads its keys and per-machine
    Codex checkout itself. Neither changes the route settings the cache keys on.
    """
    if not paid:
        return _load_offline(vault)
    from learnloop.vault.loader import load_vault

    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml; use a backup-API copy.")
    return load_vault(vault)


def _route_settings(loaded, output_tokens):
    """The explicit offline probability route and its non-secret settings."""
    route = loaded.config.ai.routing.field_llm_probability
    profile = loaded.config.ai.providers.get(route) if route else None
    if profile is None or not profile.model or not profile.model.strip():
        raise ValueError("Configure an explicit ai.routing.field_llm_probability with a model")
    subscription = is_subscription_transport(profile=profile)
    if profile.type not in METERED_ROUTE_TYPES and not subscription:
        raise ValueError(
            "Probability preparation requires an openai_chat/openrouter route (bounded physical "
            "requests) or a Codex route (subscription, estimated cost)"
        )
    endpoint = getattr(profile, "base_url", None) or (
        "https://openrouter.ai/api/v1" if profile.type == "openrouter" else ""
    )
    # Hash the endpoint: URL userinfo or query strings may carry credentials.
    settings = {
        "provider_type": profile.type, "model": profile.model,
        "endpoint_hash": sha256(endpoint.encode()).hexdigest(),
        "reasoning_effort": profile.reasoning_effort,
        "thinking": getattr(profile, "thinking", None),
        "response_format": getattr(profile, "response_format", None),
        "provider_output_tokens": getattr(profile, "max_tokens", None),
        "output_tokens": output_tokens,
    }
    return profile, settings, subscription


def prepare_or_load_zero_data(
    loaded, attempts, content, *, cache_dir, prepare=False, dry_run=False, caps: SpendCaps,
    price_per_million=None, output_tokens=256, cancelled=lambda: False,
):
    """Return ``(arms_or_None, aggregate report)``; cache-only reads build no client."""
    from learnloop.ai.execution import generation_limit
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
    from learnloop.db.repositories import Repository
    from learnloop.field import zero_data_llm as zero

    if price_per_million is not None and (
        isinstance(price_per_million, bool)
        or not math.isfinite(price_per_million) or price_per_million <= 0
    ):
        raise ValueError("--price-per-million must be finite and positive")
    if type(output_tokens) is not int or output_tokens <= 0:
        raise ValueError("--output-tokens must be a positive integer")
    summary = {"status": "disabled", "prompt_version": zero.PROMPT_VERSION, "task": zero.TASK,
               "caps": caps.as_dict(), "price_per_million": price_per_million,
               "price_source": "owner_override" if price_per_million is not None else "unknown"}
    if not (loaded.config.field.enabled and loaded.config.field.llm_probability_enabled):
        return None, summary
    profile, settings, subscription = _route_settings(loaded, output_tokens)
    attempts = tuple(attempts)
    if not prepare and dry_run:
        status = zero.cache_status(attempts, content, cache_dir=cache_dir, vault_path=loaded.root,
                                   model=profile.model, settings=settings)
        summary.update(status="dry_run", model=profile.model, **status)
        return None, summary
    if not prepare:
        arms, count = zero.load_zero_data_arms(
            attempts, content, cache_dir=cache_dir, vault_path=loaded.root,
            model=profile.model, settings=settings,
        )
        summary.update(status="complete", model=profile.model, cached=count, predictions=count)
        return arms, summary

    def prompt(request):
        return render_structured_prompt("Predict learner success", zero.PROMPT_VERSION, {
            "instructions": zero.INSTRUCTIONS, "request": request,
        })

    requests = zero.prediction_requests(attempts, content)
    # Conservative UTF-8 bound, including schema, transport envelope and output.
    tokens = max((len(prompt(request).encode()) for request in requests.values()), default=0)
    tokens += len(repr(ProbabilityResult.model_json_schema()).encode()) + 2048 + output_tokens
    client = None

    def predict(request):
        nonlocal client
        if client is None:
            resolved = ready_client_for_task(loaded.root, loaded.config, "field_llm_probability",
                                             allow_env=False)
            if resolved.client is None or not resolved.runtime.ready:
                raise AIProviderUnavailable("Configured field probability model is unavailable")
            if is_subscription_transport(client=resolved.client) != subscription:
                raise AIProviderUnavailable(
                    "Field probability model resolved to a different billing transport")
            client = resolved.client
        with generation_limit(output_tokens):
            result = execute_structured_operation(
                client, purpose=zero.TASK, prompt=prompt(request), result_model=ProbabilityResult,
            )
        return result.model_dump(mode="json")

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    repository = Repository.attach(sqlite_path, read_only=True) if dry_run else Repository(sqlite_path)
    arms, report = zero.prepare_zero_data_probabilities(
        attempts, content, repository=repository, cache_dir=cache_dir, vault_path=loaded.root,
        model=profile.model, predict=predict, settings=settings, caps=caps, dry_run=dry_run,
        cancelled=cancelled, subscription=subscription,
        estimate_per_prediction=SpendEstimate(
            calls=1, total_tokens=tokens,
            estimated_usd=None if price_per_million is None else tokens * price_per_million / 1_000_000,
        ),
    )
    report.update(price_per_million=price_per_million, price_source=summary["price_source"])
    return arms, report


def success_head_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1, help="Pre-registered: 1000.")] = 1000,
    seed: Annotated[int, typer.Option("--seed", help="Pre-registered: 0.")] = 0,
    llm_cache: Annotated[Path | None, typer.Option("--llm-cache", help="Zero-data LLM probability cache outside the vault; replay makes zero calls.")] = None,
    prepare_llm: Annotated[bool, typer.Option("--prepare-llm", help="Explicit paid preparation of the zero-data arm; requires --llm-cache and both field switches.")] = False,
    backfill_seen_stems: Annotated[bool, typer.Option("--backfill-seen-stems", help="Explicit paid step: embed (item/stem recipe, ai.routing.embedding) the exact stem each scored attempt showed, retired items and earlier wordings included. Needs both embedding switches; run alone, --dry-run first.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: coverage, and the spend estimate with --prepare-llm or --backfill-seen-stems. No calls, no writes.")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Embedding batch retries (--backfill-seen-stems only); LLM preparation never retries.")] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="USD per million tokens for this invocation's paid step: combined input/output for --prepare-llm, input for --backfill-seen-stems. Unknown prices fail closed on metered routes; a Codex route only estimates cost.")] = None,
    output_tokens: Annotated[int, typer.Option("--output-tokens", min=1)] = 256,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """T8 learner success head replay: emb_ridge's kill rule, gated heads, zero-data LLM.

    Pre-registered in docs/reviews/slice-2-t8.md. Run --dry-run first. The
    embedding arms read stored item/stem vectors for the text each attempt
    showed (--backfill-seen-stems embeds them); the LLM arms need --llm-cache
    (prepared with --prepare-llm). Arms without inputs are reported as
    unavailable. Each paid step runs in its own invocation.
    """
    from learnloop.config import MasteryConfig
    from learnloop.field.evaluation import evaluate, report_digest, write_reports
    from learnloop.field.item_content import load_content_index, seen_stem_records
    from learnloop.field.success_head import PREREGISTRATION, preregistration_hash, success_head_arms
    from learnloop.field.success_head_analysis import make_t8_analysis, summary_lines

    try:
        if prepare_llm and llm_cache is None:
            raise ValueError("--prepare-llm requires --llm-cache outside the vault")
        if prepare_llm and backfill_seen_stems:
            raise ValueError("Run --backfill-seen-stems and --prepare-llm as separate invocations")
        loaded = _load(vault, paid=(backfill_seen_stems or prepare_llm) and not dry_run)
        inputs = _replay_inputs(loaded, legacy_fallback=legacy_fallback)
        sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
        if backfill_seen_stems:
            from learnloop.cli.embeddings import _cancellation
            from learnloop.ops.embedding_backfill import backfill_embeddings

            with closing(connect(sqlite_path, read_only=True)) as connection:
                connection.execute("BEGIN")
                records = seen_stem_records(connection, loaded, inputs["attempts"])
            with _cancellation() as stop:
                backfill = backfill_embeddings(
                    loaded, dry_run=dry_run, recipes=("item/stem",), records=records,
                    caps=SpendCaps(max_candidates=max_candidates, max_calls=max_calls, max_pairs=0,
                                   max_retries=max_retries, max_total_tokens=max_tokens,
                                   max_estimated_usd=max_cost_usd),
                    price_per_million=price_per_million, cancelled=stop.is_set,
                )
            _emit({"status": backfill["status"], "backfill": backfill}, json_output)
            if backfill["status"] not in {"dry_run", "complete"}:
                raise typer.Exit(code=130 if backfill["status"] == "cancelled" else 1)
            return
        with closing(connect(sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            content, coverage = load_content_index(connection, loaded, inputs["attempts"])
        unavailable = {}
        if not coverage["difficulty"]["solver_panel"]:
            unavailable["success_head+difficulty"] = "no solver_panel difficulty (Phase 5a)"
        llm_arms, llm_report = (), None
        if llm_cache is None:
            for name in ("llm_zero_data", "llm_zero_data:recalibrated"):
                unavailable[name] = "not run: pass --llm-cache (prepared with --prepare-llm)"
        else:
            from learnloop.cli.embeddings import _cancellation

            with _cancellation() as stop:
                arms, llm_report = prepare_or_load_zero_data(
                    loaded, inputs["attempts"], content, cache_dir=llm_cache, prepare=prepare_llm,
                    dry_run=dry_run,
                    caps=SpendCaps(max_candidates=max_candidates, max_calls=max_calls, max_pairs=0,
                                   max_retries=0, max_total_tokens=max_tokens,
                                   max_estimated_usd=max_cost_usd),
                    price_per_million=price_per_million, output_tokens=output_tokens,
                    cancelled=stop.is_set,
                )
            if arms is None and not dry_run:
                _emit({"status": llm_report["status"], "llm": llm_report}, json_output)
                raise typer.Exit(code=130 if llm_report["status"] == "cancelled" else 1)
            llm_arms = arms or ()
        if dry_run:
            plan = {
                "status": "dry_run", "calls": 0, "writes": 0,
                "preregistration": {"version": PREREGISTRATION["version"], "hash": preregistration_hash()},
                "data_check": inputs["data_check"], "content": coverage,
                "unavailable": unavailable, "llm": llm_report,
            }
            _emit(plan, json_output)
            if llm_report is not None and llm_report["status"] not in {"dry_run", "complete", "disabled"}:
                raise typer.Exit(code=1)
            return
        config = loaded.config.model_dump(mode="json")
        mastery = MasteryConfig.model_validate(config["mastery"])
        t8_arms = success_head_arms(
            content, config=mastery, lo_priors=inputs["lo_priors"],
            include_difficulty="success_head+difficulty" not in unavailable,
        )
        report = evaluate(
            (*inputs["attempts"], *inputs["facets"], *inputs["signals"]),
            arms=("base_rate_lo", "mastery_ekf", "lo_general", *t8_arms, *llm_arms),
            bootstrap_samples=bootstrap_samples, seed=seed, fast_track_q=0.9,
            general_means=inputs["general_means"], lo_priors=inputs["lo_priors"], config=config,
            fsrs_weights=inputs["fsrs_weights"], fsrs_fit_id=inputs["fsrs_fit_id"],
            analyses={"t8": make_t8_analysis(unavailable=unavailable)},
        )
        report["manifest"]["embedding_model"] = coverage["embedding_model"]
        report["manifest"]["kernel"] = "bayesian_logistic_linear_blocks"
        report["manifest"]["t8"] = {
            "preregistration_hash": preregistration_hash(), "content_digest": content.digest,
            "views": coverage["views"], "dimensions": coverage["dimensions"],
        }
        report["data_check"] = inputs["data_check"]
        report["claim_priors"] = inputs["claim_priors"]
        report["t8_inputs"] = {"content": coverage, "unavailable": unavailable}
        if llm_report is not None:
            report["offline_preparation"] = llm_report
        report["vault_validation_issues"] = len(loaded.issues)
        files = write_reports(
            report, output_dir, stem="t8-success-head-" + report_digest(report)[:16],
            title="T8 learner success head replay (research only)",
            preamble=summary_lines(report["analyses"]["t8"]),
        )
        if json_output:
            _emit({"version": 1, "status": "complete", "reports": files, "evaluation": report}, True)
        else:
            typer.echo("\n".join((files["json"], files["markdown"])))
    except AIProviderUnavailable as exc:
        _emit({"status": "unavailable", "error_type": type(exc).__name__}, json_output)
        raise typer.Exit(code=1) from exc
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
