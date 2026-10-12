"""``learnloop embeddings adjudicate --task same_cause --backlog`` (Slice 2 §3.1).

Judges the blocked candidate pairs of the EXISTING hypothesis history once, so
recurrence groups cover past mistakes and not only new ones. Steps:

1. hypothesis vectors missing for the active embedding model are embedded
   first (metered, admitted against the command's caps);
2. every learner-state hypothesis is a query against the earlier ones in its
   scope; the shortlist is the live one (top-k, B3's cutoff when set,
   settled pairs skipped);
3. each shortlisted pair goes to the same-cause judge (admitted against the
   caps; Codex counts calls, metered routes also tokens and dollars), and the
   verdict is appended to ``judgment_ledger`` at once;
4. the recurrence groups are refreshed.

``--dry-run`` builds no client and sends nothing: it reports the pairs, the
vectors to embed and the spend estimate against the caps. A rerun skips every
pair already judged under the same prompt version and input.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import closing
from typing import Any

from learnloop.ai.execution import record_model_calls
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.judging import (
    EMBED_BATCH,
    EMBEDDING_ROUTE,
    default_judge_client,
    embed_on_spend,
    estimate_tokens,
    judge_executor,
    learner_state,
    plan_shortlist,
    receipt_sink,
)
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, SAME_CAUSE_ROUTE, hypothesis_subjects
from learnloop.diagnosis.split.embeddings import TASK_PREFIX, hypothesis_records
from learnloop.matching.judge import already_judged, judge_pairs, pair_input_hash, pair_prompt
from learnloop.substrate.recurrence_groups import refresh_recurrence_groups
from learnloop.vault.models import LoadedVault
MODEL_CALL_OWNER_KIND = "recurrence_backlog"
#: Output allowance of one verdict (a short JSON object).
JUDGE_OUTPUT_TOKENS = 600


def route_profile(vault: LoadedVault, route: str) -> dict[str, Any]:
    """A route's provider, model and billing from config alone (no client)."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.ai.spend import SUBSCRIPTION_PROFILE_TYPES

    config = vault.config
    selection = provider_for_task(config, route, allow_env=False)  # type: ignore[arg-type]
    profile = config.ai.providers.get(selection.provider_name)
    if route == EMBEDDING_ROUTE:
        model = config.embedding.model if config.embedding.enabled and selection.provider_name else None
    else:
        model = getattr(profile, "model", None) if profile is not None else None
    profile_type = profile.type if profile is not None else None
    return {
        "provider": selection.provider_name or None,
        "model": model,
        "max_tokens": getattr(profile, "max_tokens", None) if profile is not None else None,
        "subscription": profile_type in SUBSCRIPTION_PROFILE_TYPES,
    }


def command_spend(
    vault: LoadedVault,
    caps: SpendCaps,
    *,
    price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    embedding: bool = True,
) -> ReviewSpend:
    """One budget for the command; routes classified from config (dry-run safe)."""

    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million)
    judge = route_profile(vault, SAME_CAUSE_ROUTE)
    spend.register_profile(
        SAME_CAUSE_ROUTE, provider=judge["provider"], model=judge["model"],
        subscription=bool(judge["subscription"]), max_tokens=JUDGE_OUTPUT_TOKENS,
    )
    if embedding and vault.config.embedding.enabled:
        profile = route_profile(vault, EMBEDDING_ROUTE)
        spend.register_profile(
            EMBEDDING_ROUTE, provider=profile["provider"], model=profile["model"],
            subscription=False, max_tokens=None,
        )
    return spend


def _missing_records(repository: Repository, model_id: str) -> list[Any]:
    records = hypothesis_records(repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [
            record
            for record in records
            if get_vector(
                connection, record_kind=record.record_kind, record_id=record.record_id, field=record.field,
                content_hash=record.content_hash, model_id=model_id, task_prefix=TASK_PREFIX,
            ) is None
        ]


def plan_backlog(
    vault: LoadedVault,
    repository: Repository,
    *,
    spend: ReviewSpend,
    max_pairs: int | None = None,
    producer: str | None = None,
) -> dict[str, Any]:
    """``producer``: the judge model (an injected client's, else the configured route's)."""

    from learnloop.diagnosis.recurrence.guard import configured_judge_model

    producer = producer or configured_judge_model(vault)
    model_id = vault.config.embedding.model
    missing = _missing_records(repository, model_id) if vault.config.embedding.enabled else []
    population = hypothesis_subjects(vault, repository)
    learner = learner_state(population)
    shortlist = plan_shortlist(vault, repository, queries=learner, pool=learner, population=population, model_id=model_id)
    pairs = sorted(shortlist.pairs, key=lambda pair: (pair.left.created_at, pair.left.id, -pair.score, pair.right.id))
    with repository.connection() as connection:
        todo = [
            pair for pair in pairs
            if not already_judged(connection, SAME_CAUSE, pair.left, pair.right,
                                  input_hash=pair_input_hash(SAME_CAUSE, pair.left, pair.right), producer=producer)
        ]
    already = len(pairs) - len(todo)
    if max_pairs is not None:
        todo = todo[:max_pairs]
    judge_tokens = sum(estimate_tokens(pair_prompt(SAME_CAUSE, pair.left, pair.right)) for pair in todo)
    embed_tokens = sum(estimate_tokens(record.text) + 32 for record in missing)
    estimates = []
    if missing:
        batches = (len(missing) + EMBED_BATCH - 1) // EMBED_BATCH
        estimates.append(spend.estimate(EMBEDDING_ROUTE, calls=batches, input_tokens=embed_tokens, output_tokens=0))
    if todo:
        estimates.append(spend.estimate(
            SAME_CAUSE_ROUTE, calls=len(todo), input_tokens=judge_tokens,
            output_tokens=JUDGE_OUTPUT_TOKENS * len(todo), candidates=len(todo), pairs=len(todo),
        ))
    total = SpendEstimate(
        candidates=sum(value.candidates for value in estimates),
        pairs=sum(value.pairs for value in estimates),
        calls=sum(value.calls for value in estimates),
        total_tokens=sum(value.total_tokens for value in estimates),
        estimated_usd=None if any(value.estimated_usd is None for value in estimates) else sum(
            value.estimated_usd or 0.0 for value in estimates
        ),
    )
    admissible, reason = True, None
    try:
        spend.check(total)
    except SpendLimitExceeded as exc:
        admissible, reason = False, str(exc)
    return {
        "embedding_model": model_id,
        "judge_model": producer,
        "embeddings_enabled": bool(vault.config.embedding.enabled),
        "hypotheses": len(population),
        "learner_state_hypotheses": len(learner),
        "vectors_to_embed": len(missing),
        "shortlist": shortlist.summary(),
        "pairs_to_judge": len(todo),
        "pairs_already_judged": already,
        # Hypotheses without a vector cannot be shortlisted until embedded:
        # with vectors to embed, the pair count is a lower bound.
        "pairs_lower_bound": bool(missing),
        "estimate": {
            "calls": total.calls,
            "metered_tokens": total.total_tokens,
            "metered_usd": total.estimated_usd,
            "judge_prompt_tokens": judge_tokens,
            "embedding_tokens": embed_tokens,
        },
        "routes": {route: info.as_dict() for route, info in spend.routes.items()},
        "admissible": admissible,
        "refusal": reason,
        "_pairs": todo,
    }


def run_backlog(
    vault: LoadedVault,
    repository: Repository,
    *,
    caps: SpendCaps,
    price_per_million: float | None = None,
    max_pairs: int | None = None,
    dry_run: bool = False,
    cancelled: Callable[[], bool] | None = None,
    judge_client: Any = None,
    embedding_client: Any = None,
) -> dict[str, Any]:
    if not vault.config.embedding.enabled:
        return {
            "status": "invalid",
            "reason": "embedding.enabled is false: the backlog shortlists with hypothesis embeddings. "
            "Only validated citations and exact statements can link hypotheses without them.",
        }
    from learnloop.diagnosis.recurrence.judging import model_label

    producer = model_label(judge_client) if judge_client is not None else None
    spend = command_spend(vault, caps, price_per_million=price_per_million, cancelled=cancelled)
    plan = plan_backlog(vault, repository, spend=spend, max_pairs=max_pairs, producer=producer)
    pairs = plan.pop("_pairs")
    report: dict[str, Any] = {"status": "dry_run" if dry_run else "pending", "caps": caps.as_dict(), "plan": plan}
    if dry_run:
        return report
    if not plan["admissible"]:
        report["status"] = "over_budget"
        return report
    owner_id = repository.sqlite_path.parent.name
    # The spend collector observes every admitted call and forwards it here
    # (an inner observer replaces an outer one, so the sink is set up front).
    spend.collector.sink = receipt_sink(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=owner_id)
    with record_model_calls(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=owner_id):
        if plan["vectors_to_embed"]:
            if embedding_client is None:
                from learnloop.diagnosis.split.jobs import default_embedding_client

                embedding_client = default_embedding_client(vault)
            if embedding_client is None:
                report.update(status="provider_failed", reason="the embedding route is not ready")
                return report
            try:
                report["embedded"] = embed_on_spend(
                    spend, embedding_client, repository, _missing_records(repository, embedding_client.model_id)
                )
            except SpendLimitExceeded as exc:
                report.update(status="over_budget", reason=str(exc), spend=spend.summary())
                return report
            # The shortlist needs the new vectors: plan again (nothing sent).
            replanned = plan_backlog(vault, repository, spend=command_spend(vault, caps, price_per_million=price_per_million),
                                     max_pairs=max_pairs, producer=producer)
            pairs = replanned.pop("_pairs")
            report["replanned"] = {"pairs_to_judge": replanned["pairs_to_judge"], "shortlist": replanned["shortlist"]}
        if pairs:
            client = judge_client if judge_client is not None else default_judge_client(vault)
            if client is None:
                report.update(status="provider_failed", reason="the same-cause judge route is not ready")
                return report
            results = judge_pairs(repository, SAME_CAUSE, pairs, execute=judge_executor(spend, client))
        else:
            results = []
    report["judged"] = sum(1 for row in results if row.status == "judged")
    report["verdicts"] = {
        verdict: sum(1 for row in results if row.verdict == verdict) for verdict in ("same", "different", "unsure")
    }
    report["not_judged"] = [
        row.as_dict() for row in results if row.status in ("failed", "not_run", "claimed_elsewhere", "fenced")
    ]
    report["groups"] = refresh_recurrence_groups(vault, repository)
    report["spend"] = spend.summary()
    stopped = {row.error for row in results if row.status == "not_run"}
    report["status"] = (
        "cancelled" if "SpendCancelled" in stopped or "AIInterrupted" in stopped
        else "over_budget" if "SpendLimitExceeded" in stopped
        else "complete"
    )
    return report


__all__ = ["command_spend", "plan_backlog", "route_profile", "run_backlog"]
