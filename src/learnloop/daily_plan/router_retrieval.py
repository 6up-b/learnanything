"""Router R2c: similar past decisions (``decision/context`` embeddings, spec §5).

docs/specs/plan_router_r2_v1.md §3.7. A decision's **context** is a canonical
rendering of its typed state, read from the learner-state card it stored: the
plan's kind, re-entry and time left, the options' kinds, topics and reasons,
each topic's status, and the open problems present. It is embedded with the
Phase 1 substrate under the record kind ``decision/context``.

* **When it embeds.** The current decision's context is embedded at prefetch
  (it is also the query); the vector is written under the decision's id after
  the decision commits (the ``plan_block`` logger, in its own savepoint). The
  query embedding is a metered request like the models': the router's daily
  guard admits it before it is sent (``RouterSpend.metered``; Codex review
  F3), and a refusal is a logged ``unavailable`` (reason ``spend``).
  ``learnloop router embed-decisions`` backfills the decisions that have none
  through the shared embedding backfill (``ops.embedding_backfill``): its own
  enforced caps (calls, tokens, dollars), a priced ``--dry-run`` first, the
  embedding switches and lock, and receipts owned by ``embedding_backfill``.
* **What may be shown** (G5). A past decision qualifies only when its outcome
  had matured before the current decision's time (its R_next or R_cold
  attempt was made earlier), it was made in another session and another
  plan. Outcomes are derived on the fly from the ledgers
  (``router.outcomes.derive_router_outcomes``, the derivation ``learnloop
  router log`` uses), never read from the ``router_outcomes`` cache, which only
  a rebuild refreshes.
* **Ranking.** Mean-centred cosine among the embedded decisions
  (``db.stores.embedding_vectors.retrieve``), the top ``router.similar_k``.
  Embeddings choose what to show; they decide nothing.
* **The inclusion coin** (MemDelta discipline). Each decision flips a logged
  coin, seeded by its boundary key: with probability
  ``router.similar_include_rate`` (0.5) the models see the similar decisions,
  otherwise they are retrieved and logged but withheld, so R3 can compare the
  two on the same policy (a replay can never re-ask).
* **Gating.** Needs ``embedding.enabled`` and ``router.similar_decisions``;
  otherwise a logged no-op (``similar.status = disabled``). Replay never needs
  a vector: the ids shown are on the decision row
  (``similar_decision_ids_json``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import hashlib
import json
import logging
from typing import Any

LOG = logging.getLogger(__name__)

RECORD_KIND = "decision"
FIELD = "context"
RECIPE = f"{RECORD_KIND}/{FIELD}"
VERSION = 1
TASK_PREFIX = "retrieval-document"

DISABLED = "disabled"
INCLUDED = "included"
WITHHELD = "withheld"
UNAVAILABLE = "unavailable"


def _bucket(value: Any, edges: Sequence[float], labels: Sequence[str]) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"
    for edge, label in zip(edges, labels, strict=False):
        if number < edge:
            return label
    return labels[-1]


def context_text(card_json: Mapping[str, Any]) -> str:
    """The decision's canonical context (deterministic; no ids, no times)."""

    session = card_json.get("session") or {}
    lines = [
        f"plan: {session.get('plan_kind') or 'normal'}",
        f"re-entry after a break: {'yes' if session.get('reentry') else 'no'}",
        "time left today: " + _bucket(session.get("minutes_left"), (5, 15, 30), ("under 5 min", "5-15 min", "15-30 min", "over 30 min")),
        "days since last activity: " + _bucket(session.get("days_since_last_activity"), (1, 3, 8), ("0", "1-2", "3-7", "8 or more")),
    ]
    for candidate in card_json.get("candidates") or ():
        topics = ", ".join(sorted(str(topic) for topic in candidate.get("topics") or ())) or str(candidate.get("section") or "-")
        lines.append(
            f"option: {candidate.get('kind')} on {topics}; reason {candidate.get('reason_code')}; "
            f"{'reversible' if candidate.get('reversible', True) else 'irreversible'}"
        )
    for _lo, row in sorted((card_json.get("learning_objects") or {}).items(), key=lambda item: str(item[1].get("title") or item[0])):
        predictor = row.get("predictor") or {}
        lines.append(
            f"topic {row.get('title') or _lo}: {row.get('status') or 'unknown'}; predicted success "
            + _bucket(predictor.get("p_success"), (0.4, 0.7, 0.9), ("low", "middling", "good", "high"))
            + "; recall now " + _bucket(row.get("recall_now"), (0.5, 0.8, 0.95), ("low", "middling", "good", "high"))
        )
    problems = sorted({
        f"open problem: {entry.get('kind') or 'problem'} on {entry.get('topic') or entry.get('learning_object_id')}"
        for entry in card_json.get("open_hypotheses") or ()
    })
    lines.extend(problems)
    return "\n".join(lines)


def content_hash(text: str) -> str:
    payload = json.dumps([RECORD_KIND, FIELD, VERSION, text], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def decision_context_records(connection: Any) -> list[Any]:
    """The ``decision/context`` records of every ``plan_block`` decision whose card is stored."""

    from learnloop.vault.embedding_recipes import EmbeddingRecord

    present = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_decision_payloads'"
    ).fetchone()
    if present is None:
        return []
    records = []
    for row in connection.execute(
        "SELECT d.id AS id, p.content_json AS card FROM router_decisions d "
        "JOIN router_decision_payloads p ON p.decision_id = d.id AND p.kind = 'card' "
        "WHERE d.decision_kind = 'plan_block' ORDER BY d.created_at, d.id"
    ):
        try:
            card = json.loads(row["card"] or "null")
        except ValueError:
            continue
        if not isinstance(card, Mapping):
            continue
        text = context_text(card)
        records.append(EmbeddingRecord(RECORD_KIND, str(row["id"]), FIELD, text, content_hash(text)))
    return records


def include_coin(boundary_key: str, rate: float) -> tuple[float, bool]:
    """The decision's inclusion coin: ``(u, u < rate)``, seeded by its boundary key."""

    from learnloop.router.mixture import uniform

    u = uniform(f"similar:{boundary_key}", "coin")
    return u, u < float(rate)


def _matured(connection: Any, decision_time: str, candidate_ids: set[str], vault: Any) -> dict[str, dict[str, Any]]:
    """Of ``candidate_ids``, the decisions whose R_next or R_cold was observed
    strictly before ``decision_time``, with those outcomes."""

    from learnloop.router.outcomes import derive_router_outcomes, servable_items_by_learning_object
    from learnloop.substrate.canonical_projection import held_for_review_attempts, pfc_assessments

    if not candidate_ids:
        return {}
    attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    outcomes = derive_router_outcomes(
        connection,
        pfc_states=pfc_assessments(connection, attempt_ids),
        servable_items_by_lo=servable_items_by_learning_object(vault) if vault is not None else None,
        held_attempt_ids=held_for_review_attempts(connection),
    )
    times = {
        str(row[0]): str(row[1])
        for row in connection.execute("SELECT id, created_at FROM practice_attempts")
    }
    matured: dict[str, dict[str, Any]] = {}
    for row in outcomes:
        decision_id = str(row["decision_id"])
        if decision_id not in candidate_ids:
            continue
        observed = {}
        for name in ("r_next", "r_cold"):
            attempt = row.get(f"{name}_attempt_id")
            if row.get(f"{name}_status") == "observed" and attempt and times.get(str(attempt), "9999") < decision_time:
                observed[name] = row.get(f"{name}_value")
        if observed:
            matured[decision_id] = observed
    return matured


def _outcome_words(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "not yet seen"
    if number >= 0.999:
        return "correct"
    if number <= 0.001:
        return "incorrect"
    return f"partly correct ({number:.2f})"


def _describe(row: Mapping[str, Any], observed: Mapping[str, Any], titles: Mapping[str, str]) -> str:
    candidates = json.loads(row.get("candidates_json") or "[]")
    chosen = next((entry for entry in candidates if entry.get("ref") == row.get("chosen_ref")), {})
    topics = ", ".join(titles.get(lo, lo) for lo in chosen.get("learning_object_ids") or ()) or "-"
    offered = sum(1 for entry in candidates if entry.get("feasible") and entry.get("kind") == "block")
    chance = row.get("propensity")
    chance_text = f" (chosen with chance {float(chance):.2f})" if isinstance(chance, (int, float)) else ""
    return (
        f"- {str(row.get('created_at') or '')[:10]}: {offered} options; chose {chosen.get('lane') or chosen.get('kind') or '-'} "
        f"on {topics}{chance_text}. Next answer on that topic: {_outcome_words(observed.get('r_next'))}; "
        f"a day or more later: {_outcome_words(observed.get('r_cold'))}."
    )


def similar_decisions(
    connection: Any,
    *,
    query: Sequence[float],
    model_id: str,
    decision_time: str,
    session_id: str | None,
    plan_id: str | None,
    limit: int,
    vault: Any = None,
) -> list[dict[str, Any]]:
    """The top ``limit`` matured similar decisions (G5), each with the line shown to the models."""

    from learnloop.db.stores.embedding_vectors import retrieve

    expected: dict[str, str] = {}
    for record_id, digest in connection.execute(
        "SELECT record_id, content_hash FROM embedding_vectors WHERE record_kind = ? AND field = ? AND model_id = ? "
        "AND task_prefix = ? ORDER BY created_at, id",
        (RECORD_KIND, FIELD, model_id, TASK_PREFIX),
    ):
        expected[str(record_id)] = str(digest)
    if not expected:
        return []
    rows = {
        str(row["id"]): dict(row)
        for row in connection.execute(
            f"SELECT id, session_id, created_at, chosen_ref, propensity, candidates_json, detail_json "
            f"FROM router_decisions WHERE decision_kind = 'plan_block' AND id IN ({','.join('?' for _ in expected)})",
            tuple(expected),
        )
    }
    eligible = set()
    for decision_id, row in rows.items():
        if str(row.get("created_at") or "") >= decision_time:
            continue
        if session_id is not None and row.get("session_id") == session_id:
            continue
        try:
            detail = json.loads(row.get("detail_json") or "{}")
        except ValueError:
            detail = {}
        if plan_id is not None and detail.get("plan_id") == plan_id:
            continue
        eligible.add(decision_id)
    matured = _matured(connection, decision_time, eligible, vault)
    if not matured:
        return []
    matches = retrieve(
        connection, record_kind=RECORD_KIND, field=FIELD, model_id=model_id, task_prefix=TASK_PREFIX,
        query=query, expected_records={key: expected[key] for key in rows}, limit=limit,
        candidate_ids=set(matured),
    )
    titles = {lo_id: lo.title for lo_id, lo in (vault.learning_objects.items() if vault is not None else ())}
    return [
        {
            "decision_id": match.record_id,
            "score": round(match.score, 6),
            "outcome": matured[match.record_id],
            "line": _describe(rows[match.record_id], matured[match.record_id], titles),
        }
        for match in matches
    ]


def prepare(
    *,
    vault: Any,
    repository: Any,
    embedding_client: Any,
    card_json: Mapping[str, Any] | None,
    boundary_key: str,
    decision_time: str,
    session_id: str | None,
    plan_id: str | None,
) -> dict[str, Any]:
    """The prefetch's retrieval: embed the context, retrieve, flip the coin.

    Returns the logged record: ``status`` (``disabled`` | ``included`` |
    ``withheld`` | ``unavailable``), the coin and its rate, the ids retrieved
    and the ids shown, the lines shown, and the context vector to store
    after the decision."""

    config = vault.config.router
    rate = float(config.similar_include_rate)
    if not (bool(config.similar_decisions) and bool(vault.config.embedding.enabled)) or not card_json:
        return {"status": DISABLED}
    if embedding_client is None:
        return {"status": UNAVAILABLE, "reason": "no embedding route is ready", "rate": rate}
    from learnloop.ai.embedding import embedding_request_timeout

    from learnloop.daily_plan.router_runtime import EMBEDDING_TIMEOUT_SECONDS

    text = context_text(card_json)
    digest = content_hash(text)
    model_id = str(getattr(embedding_client, "model_id", "") or "")
    from learnloop.daily_plan.router_runtime import SpendRefused

    try:
        with embedding_request_timeout(EMBEDDING_TIMEOUT_SECONDS):
            vectors = embedding_client.embed([text], TASK_PREFIX)
        vector = [float(value) for value in vectors[0]]
    except SpendRefused:
        # The router's daily guard refused the query embedding before it was sent.
        return {"status": UNAVAILABLE, "reason": "spend", "rate": rate}
    except Exception as exc:  # noqa: BLE001 - retrieval is context; its failure is logged, never blocking
        return {"status": UNAVAILABLE, "reason": type(exc).__name__, "rate": rate}
    context_vector = {
        "record_kind": RECORD_KIND, "field": FIELD, "content_hash": digest, "model_id": model_id,
        "task_prefix": TASK_PREFIX, "vector": vector,
    }
    u, included = include_coin(boundary_key, rate)
    try:
        from learnloop.db.connection import connect

        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            import sqlite3

            connection.row_factory = sqlite3.Row
            found = similar_decisions(
                connection, query=vector, model_id=model_id, decision_time=decision_time, session_id=session_id,
                plan_id=plan_id, limit=int(config.similar_k), vault=vault,
            )
    except Exception as exc:  # noqa: BLE001
        LOG.warning("router R2c: similar decisions could not be retrieved", exc_info=True)
        return {"status": UNAVAILABLE, "reason": type(exc).__name__, "rate": rate, "context_vector": context_vector}
    retrieved = [entry["decision_id"] for entry in found]
    return {
        "status": INCLUDED if included else WITHHELD,
        "rate": rate,
        "coin": round(u, 12),
        "included": included,
        "model_id": model_id,
        "ids_retrieved": retrieved,
        "ids_shown": retrieved if included else [],
        "scores": {entry["decision_id"]: entry["score"] for entry in found},
        "lines": [entry["line"] for entry in found] if included else [],
        "context_vector": context_vector,
    }


def backfill(
    vault: Any,
    repository: Any,
    *,
    caps: Any,
    dry_run: bool,
    limit: int | None = None,
    batch_size: int = 32,
    price_per_million: float | None = None,
    client_factory: Any = None,
    cancelled: Any = None,
) -> dict[str, Any]:
    """Embed the ``decision/context`` of every logged decision that has no vector yet.

    Runs through the shared embedding backfill (``ops.embedding_backfill``,
    Codex review F3): ``caps`` (a ``SpendCaps``) is enforced before each
    request, ``dry_run`` plans with a priced estimate and sends and writes
    nothing, paid work needs ``embedding.enabled`` and
    ``embedding.backfill_enabled``, and receipts are owned by
    ``embedding_backfill``. ``limit`` embeds at most that many of the
    decisions still without a vector."""

    from learnloop.db.connection import connect
    from learnloop.db.stores.embedding_vectors import get_vector
    from learnloop.ops.embedding_backfill import backfill_embeddings
    import sqlite3

    model_id = str(vault.config.embedding.model)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        connection.row_factory = sqlite3.Row
        records = decision_context_records(connection)
        pending = [
            record for record in records
            if get_vector(connection, record_kind=RECORD_KIND, record_id=record.record_id, field=FIELD,
                          content_hash=record.content_hash, model_id=model_id, task_prefix=TASK_PREFIX) is None
        ]
    if limit is not None:
        pending = pending[: max(int(limit), 0)]
    report = backfill_embeddings(
        vault, caps=caps, dry_run=dry_run, recipes=(), batch_size=batch_size,
        price_per_million=price_per_million, cancelled=cancelled, client_factory=client_factory,
        extra_records=pending, extra_recipes=(RECIPE,),
    )
    report["recipe"] = RECIPE
    report["decisions"] = len(records)
    return report


__all__ = [
    "DISABLED",
    "FIELD",
    "INCLUDED",
    "RECIPE",
    "RECORD_KIND",
    "TASK_PREFIX",
    "UNAVAILABLE",
    "VERSION",
    "WITHHELD",
    "backfill",
    "content_hash",
    "context_text",
    "decision_context_records",
    "include_coin",
    "prepare",
    "similar_decisions",
]
