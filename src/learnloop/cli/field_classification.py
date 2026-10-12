"""Opt-in question classification command; registration is owned by field CLI."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import generation_limit
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps, SpendEstimate, is_subscription_transport
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.cli.embeddings import _cancellation
from learnloop.db.repositories import Repository
from learnloop.field.classification import PROMPT_VERSION, TASK, classify_missing_questions
from learnloop.field.signals import classification_input
from learnloop.vault.loader import load_vault
from learnloop.vault.models import learning_object_facet_union
from learnloop.vault.paths import VaultPaths


# Metered routes bound every physical request; a Codex route runs on the
# owner's subscription with estimated cost only (Slice A §5 rule 6).
METERED_ROUTE_TYPES = frozenset({"openai_chat", "openrouter"})


class QuestionClassification(WireModel):
    # Semantic validation is intentionally after the paid result is ledgered.
    question_type: str
    lo_ids: list[str]
    facets: list[str]


def register_classification_command(field_app: typer.Typer) -> None:
    field_app.command("classify-questions")(classify_questions)


def classify_questions(
    vault: Annotated[Path, typer.Option("--vault")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", help="Explicit conservative USD rate for combined input/output tokens. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.",
    )] = None,
    output_tokens: Annotated[int, typer.Option("--output-tokens", min=1)] = 512,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Classify only missing question metadata. Reruns resume cached successes.

    Requires both field switches and an explicit field_question_classifier route.
    No automatic retries/JSON repairs: a new command re-admits unfinished work.
    Dry runs load no .env/global config, construct no client and migrate nothing.
    A Codex route runs without a physical-request bound and records its cost as
    estimated_only; the candidate and call caps still apply.
    """
    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        if price_per_million is not None and (not math.isfinite(price_per_million) or price_per_million <= 0):
            raise ValueError("--price-per-million must be finite and positive")
        loaded = load_vault(vault, load_environment=False)
        route = loaded.config.ai.routing.field_question_classifier
        profile = loaded.config.ai.providers.get(route) if route else None
        if profile is None or not profile.model:
            raise ValueError("Configure an explicit ai.routing.field_question_classifier with a model")
        # Chat transports expose each physical request before I/O, so metered
        # routes keep the physical-call bound. Codex turns cannot guarantee it;
        # they are billed to the subscription and only estimate cost.
        subscription = is_subscription_transport(profile=profile)
        if profile.type not in METERED_ROUTE_TYPES and not subscription:
            raise ValueError(
                "Classification requires an openai_chat/openrouter route (bounded physical "
                "requests) or a Codex route (subscription, estimated cost)"
            )
        enabled = loaded.config.field.enabled and loaded.config.field.question_classification_enabled
        sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
        repository = (
            Repository.attach(sqlite_path, read_only=True)
            if dry_run or not enabled else Repository(sqlite_path)
        )
        events = repository.question_events()
        with repository.connection() as connection:
            cursor = connection.execute("SELECT * FROM interaction_events WHERE kind='learner_question_asked'")
            names = [c[0] for c in cursor.description]
            events += [dict(zip(names, row, strict=True)) for row in cursor]
        catalog = [
            {"id": lo.id, "title": lo.title, "summary": lo.summary,
             "facets": learning_object_facet_union(lo)}
            for lo in sorted(loaded.learning_objects.values(), key=lambda lo: lo.id)
        ]

        def prompt(row):
            return render_structured_prompt("Classify a learner question", PROMPT_VERSION, {
                "instructions": (
                    "Supply only missing metadata; retain logged types and mappings. "
                    "Types: prerequisite, mechanism, clarification, strategy, verification, other. "
                    "Curiosity or extension questions are other, not confusion. "
                    "Use only catalog LO and facet IDs; uncertain mappings must be empty. "
                    "A prerequisite question maps to the prerequisite LO, not the current item."
                ),
                "catalog": catalog, "question": row,
            })

        # UTF-8 byte count is a conservative token estimate, including the
        # schema/system envelope and bounded output. No truncation of questions.
        tokens = max((len(prompt(classification_input(e)).encode()) for e in events), default=0)
        tokens += len(QuestionClassification.model_json_schema().__repr__().encode()) + 2048 + output_tokens
        client = None

        def classify(row):
            nonlocal client
            if client is None:
                resolved = ready_client_for_task(loaded.root, loaded.config, "field_question_classifier", allow_env=False)
                if resolved.client is None or not resolved.runtime.ready:
                    raise AIProviderUnavailable("Configured field classifier is unavailable")
                if is_subscription_transport(client=resolved.client) != subscription:
                    # The admitted budget assumed the configured route's billing.
                    raise AIProviderUnavailable("Field classifier resolved to a different billing transport")
                client = resolved.client
            with generation_limit(output_tokens):
                result = execute_structured_operation(
                    client, purpose=TASK, prompt=prompt(row), result_model=QuestionClassification,
                )
            raw = result.model_dump(mode="json")
            # Preserve invalid ID verdicts in the ledger, but never cache them.
            if any(lo not in loaded.learning_objects for lo in raw["lo_ids"]) or any(
                f not in loaded.evidence_facets for f in raw["facets"]
            ):
                raw["_invalid_mapping"] = True
            return raw

        with _cancellation() as stop:
            report = classify_missing_questions(
                repository, events, model=profile.model, classify=classify,
                estimate_per_question=SpendEstimate(
                    calls=1, total_tokens=tokens,
                    estimated_usd=None if price_per_million is None else tokens * price_per_million / 1_000_000,
                ),
                caps=SpendCaps(max_candidates=max_candidates, max_calls=max_calls,
                               max_pairs=0, max_retries=0, max_total_tokens=max_tokens,
                               max_estimated_usd=max_cost_usd),
                enabled=enabled, dry_run=dry_run, cancelled=stop.is_set,
                subscription=subscription,
            )
            report["price_per_million"] = price_per_million
            report["price_source"] = "owner_override" if price_per_million is not None else "unknown"
    except (ValueError, AIProviderUnavailable, sqlite3.Error) as exc:
        report = {"status": "invalid", "error_type": type(exc).__name__}
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(130)
    if report["status"] not in {"complete", "dry_run"}:
        raise typer.Exit(1)
