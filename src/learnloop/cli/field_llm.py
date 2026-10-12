"""Explicit offline probability preparation; ordinary replay only loads cache."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import math
from pathlib import Path

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import generation_limit
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps, SpendEstimate, is_subscription_transport
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.db.repositories import Repository
from learnloop.field.offline_llm import (
    PROMPT_VERSION, TASK, prediction_requests, load_cached_probability_arm, prepare_llm_probability,
)
from learnloop.vault.paths import VaultPaths


# Metered routes bound every physical request; a Codex route runs on the
# owner's subscription with estimated cost only (Slice A §5 rule 6).
METERED_ROUTE_TYPES = frozenset({"openai_chat", "openrouter"})


class ProbabilityResult(WireModel):
    # Range validation belongs to the worker, after recording the paid verdict.
    p_success: float


def prepare_or_load_llm(
    loaded, attempts, *, cache_dir, prepare=False, dry_run=False,
    caps: SpendCaps, price_per_million, output_tokens, cancelled=lambda: False,
):
    """Return a pure cached arm and aggregate-only spend report.

    No client or repository is constructed on cache-only reads. Preparation is
    separately gated by both field switches. The worker admits the entire plan
    before invoking the lazy client. Metered routes guard every physical
    request; a Codex route runs on the subscription with estimated cost only.
    """
    if price_per_million is not None and (
        isinstance(price_per_million, bool)
        or not math.isfinite(price_per_million) or price_per_million <= 0
    ):
        raise ValueError("--price-per-million must be finite and positive")
    if type(output_tokens) is not int or output_tokens <= 0:
        raise ValueError("--output-tokens must be a positive integer")
    summary = {
        "status": "disabled", "prompt_version": PROMPT_VERSION,
        "caps": caps.as_dict(), "charged": asdict(SpendEstimate(estimated_usd=0.)),
        "price_per_million": price_per_million,
        "price_source": "owner_override" if price_per_million is not None else "unknown",
    }
    if not (loaded.config.field.enabled and loaded.config.field.llm_probability_enabled):
        return None, summary
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
    directory, vault = Path(cache_dir).resolve(), Path(loaded.root).resolve()
    if directory == vault or vault in directory.parents:
        raise ValueError("Offline probability cache must be outside the vault")
    endpoint = getattr(profile, "base_url", None) or (
        "https://openrouter.ai/api/v1" if profile.type == "openrouter" else ""
    )
    # Hash the endpoint too: URL userinfo/query strings may contain credentials.
    # Never serialize the provider profile (it can carry headers or secrets).
    settings = {
        "provider_type": profile.type, "model": profile.model,
        "endpoint_hash": sha256(endpoint.encode()).hexdigest(),
        "reasoning_effort": profile.reasoning_effort,
        "thinking": getattr(profile, "thinking", None),
        "response_format": getattr(profile, "response_format", None),
        "provider_output_tokens": getattr(profile, "max_tokens", None),
        "output_tokens": output_tokens,
    }
    attempts = tuple(attempts)
    if not prepare:
        arm = load_cached_probability_arm(
            attempts, cache_dir=directory, model=profile.model, settings=settings,
        )
        summary.update(status="complete", model=profile.model, cached=len(prediction_requests(attempts)))
        return arm, summary

    def prompt(request):
        return render_structured_prompt("Predict learner success", PROMPT_VERSION, {
            "instructions": (
                "Predict p_success strictly between zero and one using only these "
                "item features and preceding graded attempts. Do not infer the current "
                "outcome or request question text. Return only the numeric probability."
            ),
            "request": request,
        })

    # Conservative UTF-8 bound includes the schema, transport envelope and output.
    tokens = max((len(prompt(row).encode()) for row in prediction_requests(attempts).values()), default=0)
    tokens += len(repr(ProbabilityResult.model_json_schema()).encode()) + 2048 + output_tokens
    client = None

    def predict(request):
        nonlocal client
        if client is None:
            resolved = ready_client_for_task(loaded.root, loaded.config, TASK, allow_env=False)
            if resolved.client is None or not resolved.runtime.ready:
                raise AIProviderUnavailable("Configured field probability model is unavailable")
            if is_subscription_transport(client=resolved.client) != subscription:
                # The admitted budget assumed the configured route's billing.
                raise AIProviderUnavailable("Field probability model resolved to a different billing transport")
            client = resolved.client
        with generation_limit(output_tokens):
            result = execute_structured_operation(
                client, purpose=TASK, prompt=prompt(request), result_model=ProbabilityResult,
            )
        return result.model_dump(mode="json")

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    repository = Repository.attach(sqlite_path, read_only=True) if dry_run else Repository(sqlite_path)
    arm, report = prepare_llm_probability(
        attempts, repository=repository, cache_dir=directory, vault_path=vault,
        model=profile.model, predict=predict, settings=settings, caps=caps,
        enabled=True, dry_run=dry_run, cancelled=cancelled, subscription=subscription,
        estimate_per_prediction=SpendEstimate(
            calls=1, total_tokens=tokens,
            estimated_usd=None if price_per_million is None else tokens * price_per_million / 1_000_000,
        ),
    )
    report.update(price_per_million=price_per_million, price_source=summary["price_source"])
    return arm, report
