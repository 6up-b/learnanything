"""E0's named system arms on a separate service copy (spec §5.4: R0, R1').

The frozen corpus copy is never written. System arms run on a *service copy*
made from it through the backup API: production search writes its own
receipts there, and R1' needs Qwen enabled and backfilled, which changes only
that copy's ``learnloop.toml`` and database:

* ``R0``: today's effective path, the copy's own configuration (keyword-only
  when dense is off; the rewrite default as configured);
* ``R1_service_rrf``: ``search_spans`` with the ``hybrid_rrf`` pool (the
  pool ``find_sources`` forces for pagination), Qwen enabled and backfilled;
* ``R1_service_pool``: the first-page ``dense_plus_bm25`` variant.

Every paid step is admitted by the E0 ledger: embedding requests through
``LedgerEnvelope`` under the production ``spend_envelopes``, any LLM request
(the rewrite) through ``E0RequestGate``. Block hits map to the common units
(``retrieval.units_from_blocks``); their top 10 is reported apart from the
matched-unit screen.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from learnloop.ai.execution import gate_model_requests
from learnloop.ai.spend import spend_envelopes
from learnloop.db.copies import copy_tree_with_databases

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import BankQuestion
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, LedgerEnvelope
from learnloop.experiments.contextual_embeddings.callers import E0RequestGate
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot, _inside_local_root
from learnloop.experiments.contextual_embeddings.pins import RolePin
from learnloop.experiments.contextual_embeddings.retrieval import units_from_blocks


def make_service_copy(frozen_root: Path, destination: Path) -> Path:
    """A backup-API copy of a frozen copy, for the system arms."""

    if not _inside_local_root(destination):
        raise ValueError("a service copy must be under fixtures-local")
    copy_tree_with_databases(Path(frozen_root), Path(destination))
    return Path(destination)


#: The orchestrator's switches that enable embeddings on a copy (the copies predate Phase 1).
ENABLE_EMBEDDINGS = {
    "routing": {"embedding": "openrouter_embedding"},
    "profile": {"type": "openai_embedding", "base_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY"},
    "embedding": {"enabled": True, "backfill_enabled": True},
}


def enable_embeddings_on_copy(root: Path) -> None:
    """Set ``ai.routing.embedding``, the ``[ai.providers.openrouter_embedding]``
    profile and ``[embedding] enabled/backfill_enabled`` in a service copy's
    ``learnloop.toml`` (never a tracked vault: the path must be under
    fixtures-local). Refuses a copy whose embedding switches are already on."""

    import tomlkit

    root = Path(root)
    if not _inside_local_root(root):
        raise ValueError("embeddings are enabled only on copies under fixtures-local")
    toml = root / "learnloop.toml"
    document = tomlkit.parse(toml.read_text(encoding="utf-8"))
    embedding = document.get("embedding")
    if embedding is not None and embedding.get("enabled"):
        raise ValueError("embeddings are already enabled on this copy")
    ai = document.setdefault("ai", tomlkit.table())
    ai.setdefault("routing", tomlkit.table())["embedding"] = ENABLE_EMBEDDINGS["routing"]["embedding"]
    providers = ai.setdefault("providers", tomlkit.table())
    profile = tomlkit.table()
    for key, value in ENABLE_EMBEDDINGS["profile"].items():
        profile[key] = value
    providers["openrouter_embedding"] = profile
    table = document.setdefault("embedding", tomlkit.table())
    for key, value in ENABLE_EMBEDDINGS["embedding"].items():
        table[key] = value
    toml.write_text(tomlkit.dumps(document), encoding="utf-8")



def _rewrite_pin(config: Any) -> RolePin:
    """A role pin for the copy's own rewrite route: Codex is subscription;
    a metered route is priced at ``source_retrieval.llm_price_per_million``
    (unset: refused before sending by the ledger's caller)."""

    from learnloop.ai.routing import provider_for_task

    name = provider_for_task(config, "source_query_rewrite", allow_env=False).provider_name
    profile = config.ai.providers.get(name)
    subscription = getattr(profile, "type", None) in ("codex_sdk", "http", "chatgpt_plan")
    price = config.source_retrieval.llm_price_per_million
    if not subscription and price is None:
        price = float("inf")
    return RolePin("system_rewrite", name, str(getattr(profile, "type", "unknown")), str(getattr(profile, "model", "")),
                   None, "subscription" if subscription else "metered", "embeddings", 400,
                   0.0 if subscription else float(price), 0.0 if subscription else float(price),
                   "the copy's own route", "production")


def rank_system(handle: Any, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], *, arm: str,
                ledger: E0Ledger, query_text: Mapping[str, str]) -> tuple[dict[str, list[str]], dict[str, int]]:
    """``{query_id: unit ids}`` for one system arm, with dropped-hit counts."""

    from learnloop.source_retrieval.corpus import library_scope
    from learnloop.source_retrieval.search import search_spans

    pool = {"R0": None, "R1_service_rrf": "hybrid_rrf", "R1_service_pool": "dense_plus_bm25"}[arm]
    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter",
                              route=pins.EMBEDDING_PINS["qwen3_8b"].model, arm=arm)
    gate = E0RequestGate(ledger, _rewrite_pin(handle.vault.config), arm=arm)
    scope = library_scope(handle.repository)
    ranked: dict[str, list[str]] = {}
    dropped = {"withheld": 0, "unmapped": 0}
    with spend_envelopes(envelope), gate_model_requests(gate):
        for question in questions:
            result = search_spans(handle.vault, handle.repository, query_text[question.query_id], scope, deep=True,
                                  limit=pins.POOL_DEPTH, pool=pool, owner_id=f"e0:{arm}")
            keys = [(hit.extraction_id, hit.span_id) for hit in result.hits]
            units, counts = units_from_blocks(snapshot, keys)
            ranked[question.query_id] = units[: pins.POOL_DEPTH]
            for key, value in counts.items():
                dropped[key] += value
    return ranked, dropped


def backfill_service_copy(handle: Any, ledger: E0Ledger, *, client_factory: Any = None) -> list[dict[str, Any]]:
    """The production source backfill on the service copy, under the E0 ledger."""

    from learnloop.source_retrieval.source_vectors import backfill_source_vectors

    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter",
                              route=pins.EMBEDDING_PINS["qwen3_8b"].model, arm="R1_service_backfill")
    reports = []
    with spend_envelopes(envelope):
        for extraction_id in _current(handle):
            reports.append(backfill_source_vectors(handle.vault, extraction_id, client_factory=client_factory))
    return reports


def _current(handle: Any) -> list[str]:
    from learnloop.source_retrieval.corpus import current_extractions

    return sorted(current_extractions(handle.repository))


def open_service(root: Path) -> Any:
    """A service copy opened writable through the vault's own repository
    (production search writes its receipts there; never the frozen copy)."""

    from learnloop.experiments.contextual_embeddings.corpus import CopyHandle
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import vault_repository

    root = Path(root)
    if not _inside_local_root(root):
        raise ValueError("a service copy must be under fixtures-local")
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    return CopyHandle(root, vault, vault_repository(paths), Path(paths.sqlite_path))


def prepare_service_copies(frozen_root: Path, service_root: Path, ledger: E0Ledger, *,
                           client_factory: Any = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """``{"R0": handle, "R1_service": handle}`` and the backfill reports."""

    r0 = open_service(make_service_copy(frozen_root, Path(service_root) / "r0"))
    qwen_root = make_service_copy(frozen_root, Path(service_root) / "qwen")
    enable_embeddings_on_copy(qwen_root)
    qwen = open_service(qwen_root)
    return {"R0": r0, "R1_service": qwen}, backfill_service_copy(qwen, ledger, client_factory=client_factory)
