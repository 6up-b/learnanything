"""CLI adapter for the ``llm_probability`` V1-V3 arms and the judge routes.

``prepare_or_load_probability_arms`` backs ``learnloop eval --section field
--probability-arm ... --llm-cache DIR [--prepare-llm] [--dry-run]``.
``judges`` backs ``learnloop eval judges``: route resolution, readiness,
privacy disclosures, an optional free reachability probe and an optional
single, spend-capped live Decider call.

Cache-only loading and dry runs read no credentials and construct no
client. Only a real preparation (or ``--live-decider``) loads the machine's
keys, the way the app itself does.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
from pathlib import Path
from typing import Any, Sequence

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.routing import provider_for_task, ready_client_for_task, route_profile_mismatch
from learnloop.ai.spend import SpendCaps, is_subscription_transport
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION
from learnloop.db.connection import connect
from learnloop.field.probability_arms import JUDGES, arm_name
from learnloop.field.probability_prep import (
    DECIDER_OUTPUT_TOKENS, JudgeRoute, check_cache_location, load_arms, prediction_points,
    prepare_judge, render_plan,
)
from learnloop.field.probability_states import StateRenderer
from learnloop.vault.paths import VaultPaths

#: The two routes' task names (router spec §6.2).
ROUTE_TASKS = {"decider": "llm_probability_decider", "llm": "llm_probability_llm"}
ROUTER_TASKS = {"decider": "router_decider", "llm": "router_llm"}
METERED_LLM_TYPES = frozenset({"openai_chat", "openrouter"})


def load_machine_environment(vault_root: Path) -> None:
    """Load keys the way the app does: the vault .env, then settings.env.

    Never overrides the process environment and never prints a value. Used
    only right before a paid call; replay and dry runs never reach it.
    """

    from learnloop.config.loader import global_settings_path, load_dotenv

    load_dotenv(Path(vault_root) / ".env")
    load_dotenv(global_settings_path())


def _endpoint_hash(value: str | None) -> str:
    # URL userinfo or query strings may hold credentials: hash, never store.
    return sha256((value or "").encode()).hexdigest()


def resolve_route(loaded, judge: str, *, price_per_million: float | None, output_tokens: int,
                  task: str | None = None) -> JudgeRoute:
    """The configured route for a judge, without credentials or a client."""

    config = loaded.config
    task = task or ROUTE_TASKS[judge]
    # The offline harness follows the vault's configuration only: an unset
    # LLM route is the active provider, never a shell or settings.env
    # LEARNLOOP_AI_PROVIDER that the dry run and the paid run could see
    # differently (Phase 2's offline rule).
    selection = provider_for_task(config, task, allow_env=False)
    name = selection.provider_name
    profile = config.ai.providers.get(name) if name else None
    if profile is None:
        raise ValueError(f"ai.routing.{task} names no configured provider ({name or 'unset'})")
    mismatch = route_profile_mismatch(config, name, task)
    if mismatch:
        raise ValueError(mismatch)
    if judge == "decider":
        from learnloop.ai.providers.decider import resolved_decider_settings

        settings = resolved_decider_settings(profile)
        return JudgeRoute(
            judge="decider", provider=name, model=settings.model,
            settings={"provider_type": "decider", "api": settings.api, "model": settings.model,
                      "endpoint_hash": _endpoint_hash(settings.url)},
            subscription=False, price_per_million=settings.price_per_million_input,
            output_tokens=DECIDER_OUTPUT_TOKENS,
            client_factory=lambda: _decider_client(loaded, task, name),
        )
    if not profile.model or not profile.model.strip():
        raise ValueError(f"ai.routing.{task} resolves to {name!r}, which names no model")
    subscription = is_subscription_transport(profile=profile)
    if profile.type not in METERED_LLM_TYPES and not subscription:
        raise ValueError(
            f"{name!r} ({profile.type}) cannot serve the LLM judge: use an openai_chat/openrouter "
            "profile (bounded physical requests) or a Codex profile (subscription, estimated cost)"
        )
    endpoint = getattr(profile, "base_url", None) or (
        "https://openrouter.ai/api/v1" if profile.type == "openrouter" else ""
    )
    return JudgeRoute(
        judge="llm", provider=name, model=profile.model,
        settings={
            "provider_type": profile.type, "model": profile.model, "endpoint_hash": _endpoint_hash(endpoint),
            "reasoning_effort": profile.reasoning_effort, "thinking": getattr(profile, "thinking", None),
            "response_format": getattr(profile, "response_format", None),
            "provider_output_tokens": getattr(profile, "max_tokens", None), "output_tokens": output_tokens,
        },
        subscription=subscription, price_per_million=price_per_million, output_tokens=output_tokens,
        client_factory=lambda: _llm_client(loaded, task, name, subscription),
    )


def _decider_client(loaded, task: str, name: str):
    load_machine_environment(loaded.root)
    resolved = ready_client_for_task(loaded.root, loaded.config, task, explicit=name)
    if resolved.client is None or not resolved.runtime.ready:
        raise AIProviderUnavailable(resolved.runtime.message or "The Decider route is not ready")
    return resolved.client


def _llm_client(loaded, task: str, name: str, subscription: bool):
    load_machine_environment(loaded.root)
    # Pin the planned route: a fallback must not change the admitted plan.
    resolved = ready_client_for_task(loaded.root, loaded.config, task, explicit=name)
    if resolved.client is None or not resolved.runtime.ready:
        raise AIProviderUnavailable(resolved.runtime.message or "The LLM judge route is not ready")
    client = resolved.client
    if is_subscription_transport(client=client) != subscription:
        raise AIProviderUnavailable("The LLM judge resolved to a different billing transport")
    if not subscription and not client.supports(BOUNDED_STRUCTURED_COMPLETION):
        raise AIProviderUnavailable("The LLM judge transport cannot bound physical requests")
    return client


def prepare_or_load_probability_arms(
    loaded, inputs: dict[str, Any], *, cache_dir: Path, selection: Sequence[tuple[str, str]],
    prepare: bool = False, dry_run: bool = False, caps: SpendCaps,
    price_per_million: float | None, output_tokens: int, cancelled=lambda: False,
    routes: dict[str, JudgeRoute] | None = None,
) -> tuple[list[Any], dict[str, Any]]:
    """Return ``(arms, aggregate report)``; arms is empty unless complete.

    Requires ``field.enabled`` and ``field.llm_probability_enabled`` (D8).
    The report holds counts, estimates and model ids, never learner text.
    """

    report: dict[str, Any] = {
        "status": "disabled", "selection": [f"{v}/{j}" for v, j in selection],
        "arms": [arm_name(v, j, recalibrated=r) for v, j in selection for r in (False, True)],
        "caps_per_judge": caps.as_dict(), "judges": {},
    }
    if not (loaded.config.field.enabled and loaded.config.field.llm_probability_enabled):
        report["reason"] = "Enable field.enabled and field.llm_probability_enabled (both off by default, D8)."
        return [], report
    if type(output_tokens) is not int or output_tokens <= 0:
        raise ValueError("--output-tokens must be a positive integer")
    directory = check_cache_location(cache_dir, loaded.root)
    judges = [judge for judge in JUDGES if any(j == judge for _, j in selection)]
    variants = tuple(dict.fromkeys(v for v, _ in selection))
    routes = routes or {
        judge: resolve_route(loaded, judge, price_per_million=price_per_million, output_tokens=output_tokens)
        for judge in judges
    }
    incumbent = {
        "config": loaded.config.mastery,
        "general_means": inputs.get("general_means"), "lo_priors": inputs.get("lo_priors"),
    }
    points = prediction_points((*inputs["attempts"], *inputs["signals"]), incumbent=incumbent)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    # Render everything from one read-only snapshot, then close it before
    # any write: receipts and judgments need the database unlocked.
    with closing(connect(sqlite_path, read_only=True)) as connection:
        connection.execute("BEGIN")
        plan = render_plan(points, variants, StateRenderer(loaded, connection))
    report.update(predictions=len(points), cache_dir_outside_vault=True)
    if prepare or dry_run:
        from learnloop.db.repositories import Repository

        repository = None if dry_run else Repository(sqlite_path)
        for judge in judges:
            judge_variants = [v for v, j in selection if j == judge]
            report["judges"][judge] = prepare_judge(
                plan, route=routes[judge], variants=judge_variants, cache_dir=directory,
                repository=repository, caps=caps, dry_run=dry_run, cancelled=cancelled,
            )
        statuses = {value["status"] for value in report["judges"].values()}
        if dry_run:
            report["status"] = "dry_run" if statuses <= {"dry_run"} else "over_budget"
            report["estimate_total"] = _total_estimate(report["judges"].values())
            return [], report
        if statuses - {"complete"}:
            report["status"] = next(s for s in ("cancelled", "over_budget", "unavailable", "provider_failed",
                                                "incomplete") if s in statuses)
            return [], report
    arms, loaded_report = load_arms(plan, cache_dir=directory, routes=routes, selection=selection)
    report.update(cache=loaded_report)
    if loaded_report["missing"]:
        report["status"] = "incomplete"
        report["reason"] = "Prepared probabilities are missing; run with --prepare-llm (dry-run first)."
        return [], report
    report["status"] = "complete"
    return arms, report


def _total_estimate(judge_reports) -> dict[str, Any]:
    usd: float | None = 0.0
    calls = tokens = 0
    for value in judge_reports:
        estimate = value.get("estimate") or {}
        calls += int(estimate.get("calls") or 0)
        tokens += int(estimate.get("total_tokens") or 0)
        if estimate.get("estimated_usd") is None:
            usd = None
        elif usd is not None:
            usd += float(estimate["estimated_usd"])
    return {"calls": calls, "total_tokens": tokens, "estimated_usd": usd,
            "note": "Subscription (Codex) estimates are tokens only unless a price is given."}


def pairwise_comparisons(selection: Sequence[tuple[str, str]]) -> list[tuple[str, str]]:
    """V2 vs V1, V3 vs V2, V3 vs V1 within each judge; LLM vs Decider per variant.

    Each pair is (baseline, challenger), for raw and recalibrated arms.
    """

    chosen = set(selection)
    pairs: list[tuple[str, str]] = []
    for recal in (False, True):
        for judge in JUDGES:
            for base, challenger in (("v1", "v2"), ("v2", "v3"), ("v1", "v3")):
                if (base, judge) in chosen and (challenger, judge) in chosen:
                    pairs.append((arm_name(base, judge, recalibrated=recal),
                                  arm_name(challenger, judge, recalibrated=recal)))
        for variant in ("v1", "v2", "v3"):
            if (variant, "decider") in chosen and (variant, "llm") in chosen:
                pairs.append((arm_name(variant, "llm", recalibrated=recal),
                              arm_name(variant, "decider", recalibrated=recal)))
    return pairs




# -- `learnloop eval judges` -------------------------------------------------

READINESS_QUESTION_SET = "judge_readiness_v1"


def judge_readiness(loaded, *, probe: bool = False, http=None) -> dict[str, Any]:
    """Route resolution, key presence, disclosures; ``probe`` adds a free GET."""

    from learnloop.ai.disclosures import JUDGE_ROUTES, judge_route_disclosures
    from learnloop.ai.routing import runtime_for_provider

    config = loaded.config
    field_on = bool(config.field.enabled and config.field.llm_probability_enabled)
    disclosures = {entry["route"]: entry for entry in judge_route_disclosures(config)}
    routes = []
    for task, judge, consumer in JUDGE_ROUTES:
        selection = provider_for_task(config, task, allow_env=consumer != "llm_probability")  # type: ignore[arg-type]
        name = selection.provider_name
        profile = config.ai.providers.get(name) if name else None
        runtime = runtime_for_provider(loaded.root, config, name, task=task)  # type: ignore[arg-type]
        entry: dict[str, Any] = {
            "route": task, "judge": judge, "consumer": consumer,
            "configured": getattr(config.ai.routing, task) or None,
            "provider": name or None, "provider_type": profile.type if profile is not None else None,
            "model": runtime.model, "ready": runtime.ready, "status": runtime.status,
            "message": runtime.message,
            "billing": ("subscription" if profile is not None and is_subscription_transport(profile=profile)
                        else "metered" if profile is not None else None),
            "falls_back": judge == "llm",
            "consumer_status": (
                ("on" if field_on else "off (field.enabled and field.llm_probability_enabled)")
                if consumer == "llm_probability" else "no consumer until router R2"
            ),
            "disclosure": disclosures[task]["disclosure"],
        }
        if probe and profile is not None and profile.type == "decider":
            from learnloop.ai.providers.decider import probe_decider_endpoint

            try:
                entry["probe"] = probe_decider_endpoint(profile, http=http)
            except AIProviderUnavailable as exc:
                entry["probe"] = {"reachable": False, "checked": True, "message": str(exc)}
        routes.append(entry)
    return {"version": 1, "routes": routes}


def live_decider_check(loaded, *, task: str = "llm_probability_decider", http=None) -> dict[str, Any]:
    """One minimal, spend-capped Decider call that carries no learner data.

    It confirms the endpoint, the request body and the typed answer. The call
    is receipted in the vault's database (``owner_kind = "judge_readiness"``);
    it is not a verdict about the learner, so nothing enters judgment_ledger.
    """

    from dataclasses import asdict

    from learnloop.ai.decisions import NoulQuestion, ScoreQuestion, ChoiceQuestion, request_body
    from learnloop.ai.execution import call_labels, observe_model_calls
    from learnloop.ai.providers.decider import DeciderProviderClient, estimate_input_tokens
    from learnloop.ai.spend import SpendBudget, SpendEstimate
    from learnloop.db.repositories import Repository
    from learnloop.ids import new_ulid

    load_machine_environment(loaded.root)
    name = provider_for_task(loaded.config, task).provider_name  # type: ignore[arg-type]
    mismatch = route_profile_mismatch(loaded.config, name, task)  # type: ignore[arg-type]
    if mismatch:
        raise ValueError(mismatch)
    profile = loaded.config.ai.providers[name]
    client = DeciderProviderClient(name, profile, http=http)
    state = "LearnLoop readiness check. This text contains no learner data."
    questions = {
        "is_check": NoulQuestion(instructions="Is this text a software readiness check?"),
        "kind": ChoiceQuestion(
            instructions="What kind of text is this?",
            options={"readiness_check": "A test message from software", "learner_answer": None},
        ),
        "clarity": ScoreQuestion(instructions="How clear is the text?", levels=("unclear", "clear")),
    }
    tokens = estimate_input_tokens(request_body(client.model, state, questions))
    caps = SpendCaps(max_candidates=1, max_pairs=0, max_retries=0, max_calls=1,
                     max_total_tokens=4_000, max_estimated_usd=0.001)
    budget = SpendBudget(caps)
    estimate = SpendEstimate(candidates=1, calls=1, total_tokens=tokens + DECIDER_OUTPUT_TOKENS,
                             estimated_usd=client.estimated_cost(tokens))
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    owner_id = new_ulid()
    with budget.request(estimate) as charge, observe_model_calls(
        lambda action, event: repository.record_model_event(
            action, event, owner_kind="judge_readiness", owner_id=owner_id)
    ), call_labels(judge="decider", question_set_version=READINESS_QUESTION_SET):
        result = client.decide(state, questions, purpose="judge_readiness")
        charge.reconcile(total_tokens=result.input_tokens + result.output_tokens,
                         estimated_usd=result.cost if result.cost is not None else client.estimated_cost(result.input_tokens))
    answers = {}
    for key, answer in result.answers.items():
        answers[key] = {k: (dict(v) if isinstance(v, dict) else v) for k, v in asdict(answer).items()}
    return {
        "status": "complete", "provider": name, "url": client.settings.url,
        "requested_model": client.model, "resolved_model": result.model,
        "response_id": result.response_id, "answered_by": result.provider,
        "answers": answers,
        "usage": {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                  "cost_usd": result.cost},
        "caps": caps.as_dict(), "charged": asdict(budget.used),
        "receipt_owner": {"owner_kind": "judge_readiness", "owner_id": owner_id},
    }


__all__ = [
    "ROUTE_TASKS",
    "ROUTER_TASKS",
    "load_machine_environment",
    "pairwise_comparisons",
    "prepare_or_load_probability_arms",
    "judge_readiness",
    "live_decider_check",
    "resolve_route",
]
