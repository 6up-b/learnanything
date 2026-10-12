"""S1.4a/S1.4b embeddings for the diagnoser (Slice 1 §9.3, §9.5).

Three record kinds, all LLM-written or canonical text, never a raw answer
alone (§9.3):

* ``hypothesis/statement`` - a candidate-cause statement plus its mechanism
  slug, embedded whenever ``embedding.enabled`` (would-merge log);
* ``misconception/statement`` - durable registry beliefs and legacy
  holding-pen rows (canonical vaults' holding pen IS the hypothesis set);
* ``attempt/divergence`` - the item stem, first-divergence quotes, error types
  and the blind grader's local-analysis excerpt, only when
  ``diagnosis.history_mode = "hybrid"`` (S1.4b).

Vectors go through the Phase 1 store (content-hash idempotent). Live writes
are small and capped per job; the backfill reuses the Phase 1 command. Nothing
here is evidence, nothing here decides identity (Slice 2 R1): the would-merge
log only records nearest neighbours next to the exact-key group, in shadow.
"""

from __future__ import annotations

import hashlib
import logging
import json
from contextlib import closing
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from learnloop.ai.embedding import EmbeddingClient
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector, put_vector, retrieve
from learnloop.recurrence import recurrence_key
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.vault.embedding_recipes import EmbeddingRecord
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

LOG = logging.getLogger(__name__)

TASK_PREFIX = "retrieval-document"
HYPOTHESIS_KIND, HYPOTHESIS_FIELD, HYPOTHESIS_VERSION = "hypothesis", "statement", 1
MISCONCEPTION_KIND, MISCONCEPTION_FIELD, MISCONCEPTION_VERSION = "misconception", "statement", 1
DIVERGENCE_KIND, DIVERGENCE_FIELD = "attempt", "divergence"
DB_RECIPES = ("hypothesis/statement", "misconception/statement", "attempt/divergence")
WOULD_MERGE_LIMIT = 5
#: Live embed-on-write caps per job (metered route; the backfill has its own).
LIVE_CAPS = SpendCaps(
    max_candidates=200,
    max_pairs=0,
    max_retries=1,
    max_calls=4,
    max_total_tokens=200_000,
    max_estimated_usd=0.05,
)
PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}


def _record(kind: str, field: str, version: int, record_id: str, text: str) -> EmbeddingRecord:
    payload = json.dumps([kind, field, version, text], ensure_ascii=False, separators=(",", ":"))
    return EmbeddingRecord(
        kind, record_id, field, text, hashlib.sha256(payload.encode("utf-8")).hexdigest()
    )


def hypothesis_text(row: Mapping[str, Any]) -> str:
    """Statement + mechanism slug (§9.3)."""

    evidence = row.get("evidence") if isinstance(row.get("evidence"), Mapping) else {}
    projection = evidence.get("mechanism_projection") if isinstance(evidence, Mapping) else None
    slug = row.get("operation") or (
        projection.get("mechanism") if isinstance(projection, Mapping) else None
    )
    statement = str(row.get("statement") or "").strip()
    return f"{statement}\nMechanism: {slug}" if slug else statement


def hypothesis_records(
    repository: Repository, *, attempt_ids: Iterable[str] | None = None
) -> list[EmbeddingRecord]:
    """Current heads of every concrete hypothesis (open-set arms excluded)."""

    wanted = set(attempt_ids) if attempt_ids is not None else None
    with repository.connection() as connection:
        rows = [
            dict(row)
            for row in connection.execute(
                """
                SELECT h.* FROM causal_hypotheses h
                 WHERE h.status != 'open_set'
                   AND h.version = (
                     SELECT MAX(head.version) FROM causal_hypotheses head
                      WHERE head.episode_key = h.episode_key
                   )
                 ORDER BY h.created_at, h.id
                """
            )
        ]
    records: list[EmbeddingRecord] = []
    for row in rows:
        if wanted is not None and str(row.get("attempt_id")) not in wanted:
            continue
        try:
            row["evidence"] = json.loads(row.get("evidence_json") or "{}")
        except (TypeError, ValueError):
            row["evidence"] = {}
        text = hypothesis_text(row)
        if text.strip():
            records.append(
                _record(HYPOTHESIS_KIND, HYPOTHESIS_FIELD, HYPOTHESIS_VERSION, str(row["episode_key"]), text)
            )
    return records


def misconception_record(record_id: str, statement: str) -> EmbeddingRecord | None:
    """The ``misconception/statement`` record of one registry entry.

    ``record_id`` is ``durable:<id>`` or ``candidate:<id>``. Embed-on-write,
    the backfill and the diagnosis registry shortlist all key vectors this
    way, so a vector one of them paid for is reused by the others.
    """

    text = str(statement or "").strip()
    if not text:
        return None
    return _record(MISCONCEPTION_KIND, MISCONCEPTION_FIELD, MISCONCEPTION_VERSION, record_id, text)


def misconception_records(repository: Repository) -> list[EmbeddingRecord]:
    """Durable beliefs plus legacy holding-pen rows (§9.3)."""

    records: list[EmbeddingRecord] = []
    with repository.connection() as connection:
        for row in connection.execute("SELECT id, statement FROM misconceptions ORDER BY created_at, id"):
            record = misconception_record(f"durable:{row[0]}", row[1])
            if record is not None:
                records.append(record)
        for row in connection.execute(
            "SELECT id, statement FROM misconception_candidates WHERE status = 'candidate' ORDER BY created_at, id"
        ):
            record = misconception_record(f"candidate:{row[0]}", row[1])
            if record is not None:
                records.append(record)
    return records


def divergence_records(
    vault: LoadedVault, repository: Repository, *, attempt_ids: Iterable[str] | None = None
) -> list[EmbeddingRecord]:
    """``attempt/divergence`` for blind-graded non-pass attempts (S1.4b)."""

    from learnloop.diagnosis.split.live import live_history_store
    from learnloop.diagnosis.split.retrieval import attempt_divergence_text, content_hash

    wanted = set(attempt_ids) if attempt_ids is not None else None
    store = live_history_store(vault, repository)
    records: list[EmbeddingRecord] = []
    for attempt in store.all_attempts():
        if wanted is not None and attempt.attempt_id not in wanted:
            continue
        if not attempt.non_pass:
            continue
        text = attempt_divergence_text(attempt)
        records.append(EmbeddingRecord(DIVERGENCE_KIND, attempt.attempt_id, DIVERGENCE_FIELD, text, content_hash(text)))
    return records


def db_records(vault: LoadedVault, repository: Repository, selectors: Sequence[str]) -> list[EmbeddingRecord]:
    """Records for the DB-backed recipes a backfill selector names."""

    out: list[EmbeddingRecord] = []
    for selector in selectors:
        if selector in ("hypothesis", "hypothesis/statement"):
            out.extend(hypothesis_records(repository))
        elif selector in ("misconception", "misconception/statement"):
            out.extend(misconception_records(repository))
        elif selector in ("attempt", "attempt/divergence"):
            out.extend(divergence_records(vault, repository))
        else:
            raise ValueError(f"Unknown embedding recipe: {selector}")
    return out


def is_db_selector(selector: str) -> bool:
    return selector in {*DB_RECIPES, "hypothesis", "misconception", "attempt"}


def backfill_with_db_recipes(
    loaded: LoadedVault, *, recipes: Sequence[str] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """``learnloop embeddings backfill`` with Slice 1's DB-backed recipes.

    Vault recipes (facet, item) go through the Phase 1 path unchanged; the
    hypothesis/misconception/attempt selectors are built here from the
    database and embedded under the same caps, checkpoints and receipts.
    """

    selectors = list(recipes or ())
    db_selectors = [value for value in selectors if is_db_selector(value)]
    vault_selectors = [value for value in selectors if not is_db_selector(value)]
    if not db_selectors:
        return backfill_embeddings(loaded, recipes=tuple(selectors) if recipes is not None else None, **kwargs)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not sqlite_path.exists():
        raise ValueError("The vault has no state database to read hypotheses from")
    records = db_records(loaded, Repository.attach(sqlite_path, read_only=True), db_selectors)
    return backfill_embeddings(
        loaded,
        recipes=tuple(vault_selectors),
        extra_records=records,
        extra_recipes=db_selectors,
        **kwargs,
    )


def _identity(record: EmbeddingRecord, model_id: str) -> dict[str, str]:
    return {
        "record_kind": record.record_kind,
        "record_id": record.record_id,
        "field": record.field,
        "content_hash": record.content_hash,
        "model_id": model_id,
        "task_prefix": TASK_PREFIX,
    }


def pending_records(repository: Repository, records: Sequence[EmbeddingRecord], model_id: str) -> list[EmbeddingRecord]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [record for record in records if get_vector(connection, **_identity(record, model_id)) is None]


@dataclass
class EmbedResult:
    embedded: int = 0
    pending: int = 0
    status: str = "complete"
    error: str | None = None


def embed_records(
    client: EmbeddingClient,
    repository: Repository,
    records: Sequence[EmbeddingRecord],
    *,
    caps: SpendCaps = LIVE_CAPS,
    batch_size: int = 32,
) -> EmbedResult:
    """Embed missing records under a per-job budget; saved batches persist."""

    model_id = client.model_id
    pending = pending_records(repository, records, model_id)
    result = EmbedResult(pending=len(pending))
    if not pending:
        return result
    price = PRICES_PER_MILLION.get(model_id)
    budget = SpendBudget(caps)
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset:offset + batch_size]
        tokens = sum(len(record.text.encode("utf-8")) + 128 for record in batch)
        estimate = SpendEstimate(
            candidates=len(batch),
            calls=1,
            total_tokens=tokens,
            estimated_usd=(tokens * price / 1_000_000) if price is not None else None,
        )
        try:
            with budget.request(estimate):
                vectors = client.embed([record.text for record in batch], TASK_PREFIX)
        except Exception as exc:  # noqa: BLE001 - best effort; the job records it
            LOG.warning("embedding batch failed (%s)", type(exc).__name__, exc_info=True)
            result.status = "failed"
            result.error = type(exc).__name__
            return result
        if len(vectors) != len(batch) or any(len(vector) != client.dims for vector in vectors):
            result.status = "failed"
            result.error = "invalid_response"
            return result
        with closing(connect(repository.sqlite_path)) as connection, connection:
            for record, vector in zip(batch, vectors, strict=True):
                put_vector(connection, **_identity(record, model_id), vector=vector)
        result.embedded += len(batch)
    return result


def _hypothesis_rows(repository: Repository, episode_keys: Iterable[str]) -> list[dict[str, Any]]:
    rows = []
    for key in episode_keys:
        head = repository.latest_causal_hypothesis_for_episode(str(key))
        if head is not None and head.get("status") != "open_set":
            rows.append(head)
    return rows


def _facets(row: Mapping[str, Any]) -> set[str]:
    ref = row.get("target_ref")
    if isinstance(ref, Mapping) and ref.get("kind") == "facet_capability" and ref.get("facet_id"):
        return {str(ref["facet_id"])}
    return set()


def record_would_merge(
    repository: Repository,
    *,
    diagnosis_id: str | None,
    attempt_id: str,
    model_id: str,
) -> int:
    """§9.5: nearest prior hypotheses for each hypothesis this attempt minted.

    Facet-filtered before ranking (same target facet, else same LO), restricted
    to hypotheses minted by EARLIER attempts, mean-centred over every current
    hypothesis vector of this model. Logged next to the exact-key group; read
    by nothing that routes. Returns how many rows were written.
    """

    all_records = hypothesis_records(repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        present = {
            record.record_id: record.content_hash
            for record in all_records
            if get_vector(connection, **_identity(record, model_id)) is not None
        }
    if not present:
        return 0
    heads = {
        str(row["episode_key"]): row
        for row in _hypothesis_rows(repository, present)
    }
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    cutoff = (str(attempt.get("created_at") or ""), attempt_id)
    attempt_rows: dict[str, tuple[str, str]] = {}
    written = 0
    for key, row in heads.items():
        if str(row.get("attempt_id")) != attempt_id:
            continue
        exact_key = recurrence_key(row)
        facets = _facets(row)
        candidates = []
        exact_group = []
        for other_key, other in heads.items():
            if other_key == key:
                continue
            other_attempt = str(other.get("attempt_id") or "")
            if other_attempt not in attempt_rows:
                fetched = repository.fetch_practice_attempt(other_attempt) or {}
                attempt_rows[other_attempt] = (str(fetched.get("created_at") or ""), other_attempt)
            if attempt_rows[other_attempt] >= cutoff:
                continue
            other_facets = _facets(other)
            same_scope = bool(facets & other_facets) if facets and other_facets else (
                str(other.get("learning_object_id")) == str(row.get("learning_object_id"))
            )
            if not same_scope:
                continue
            candidates.append(other_key)
            if recurrence_key(other) == exact_key:
                exact_group.append(str(other.get("id")))
        neighbors: list[dict[str, Any]] = []
        if candidates:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                query = get_vector(connection, **_identity(
                    EmbeddingRecord(HYPOTHESIS_KIND, key, HYPOTHESIS_FIELD, "", present[key]), model_id
                ))
                if query is None:
                    continue
                matches = retrieve(
                    connection,
                    record_kind=HYPOTHESIS_KIND,
                    field=HYPOTHESIS_FIELD,
                    model_id=model_id,
                    task_prefix=TASK_PREFIX,
                    query=query,
                    expected_records=present,
                    limit=WOULD_MERGE_LIMIT,
                    candidate_ids=candidates,
                )
            for rank, match in enumerate(matches, start=1):
                other = heads.get(match.record_id) or {}
                neighbors.append(
                    {
                        "hypothesis_id": other.get("id"),
                        "episode_key": match.record_id,
                        "attempt_id": other.get("attempt_id"),
                        "cosine": round(match.score, 6),
                        "rank": rank,
                        "same_exact_key": recurrence_key(other) == exact_key,
                    }
                )
        if repository.insert_would_merge(
            diagnosis_id=diagnosis_id,
            hypothesis_id=str(row.get("id")),
            model_id=model_id,
            exact_key=exact_key,
            exact_group_ids=exact_group,
            neighbors=neighbors,
        ):
            written += 1
    return written


__all__ = [
    "DB_RECIPES",
    "EmbedResult",
    "LIVE_CAPS",
    "db_records",
    "divergence_records",
    "embed_records",
    "hypothesis_records",
    "hypothesis_text",
    "backfill_with_db_recipes",
    "is_db_selector",
    "misconception_records",
    "pending_records",
    "record_would_merge",
]
