"""Adaptive hints H2b: outcome placement (spec_adaptive_hints_v1 §6.1, §7.2-7.3, D11).

On the practice screen a wrong answer after a hint does not say whether the
learner got past the hint's target. For a hinted attempt submitted **not
fully correct** on an item with a current approach map, one small background
call (route ``hint_outcome``) places the final answer on the map: the route
it follows and the last node it reaches, with the answer's own words that
reach it. Each shown hint of the attempt is then judged in code: ``reached``
(its target node, or for a kind without one the next node from where it was
placed, lies at or before the answer's node on the answer's route),
``not_reached`` (it lies after it), or ``unknown`` with the reason (the answer
follows no route of the map, the hint's target is on another route, the
answer could not be placed).

**Measurement only.** Nothing here touches the grade, the diagnosis or
evidence: the verdicts are ``judgment_ledger`` rows (task ``hint_outcome``,
judge ``llm``, one per shown hint row, left ``help_assist`` / right
``practice_attempt``, the placement in the rationale) that only ``learnloop
hints report`` reads. No new table, and ``help_assists`` is not updated.

**Background, never on a request path.** :func:`schedule_outcome_placement`
is called after the submit's response is built, returns at once and never
raises; the work runs in H1's :class:`~learnloop.hints.map_builder.BackgroundBuilds`
registry (the sidecar's, bound to the loaded vault: a vault switch,
``shutdown`` or EOF stops admitting it and fences its late writes), under a
durable claim (``hint_outcome:<attempt id>`` on ``judgment_work_claims``,
H1's lease and heartbeat) and through H1's fenced repository, so a placement
is paid for once across processes and never lands in another vault. Codex is
allowed (background work). A metered call joins the maps' envelope
``hints.maps.max_daily_cost_usd`` at ``hints.price_per_million`` (unset: refused
before sending).

**Switches.** ``hints.outcome_placement_enabled`` (the kill switch, default
on per D11), ``hints.adaptive_enabled`` with the telemetry its rows need,
``hints.maps.enabled`` (no map, nothing to place on). Without an injected
client, ``LEARNLOOP_APPROACH_MAP_BUILDS=off`` or ``LEARNLOOP_HINT_MODELS=off``
(both set by the test suite, and on a vault copy run) starts nothing.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, field
import json
import logging
import os
from pathlib import Path
import threading
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendLimitExceeded, spend_envelopes
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.hints import map_builder as maps
from learnloop.hints.writer import models_off
from learnloop.practice_index.paid import PaidCalls, plan_route, resolve_client
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

ROUTE_TASK = "hint_outcome"
PURPOSE = "hint_outcome"
OWNER_KIND = maps.OUTCOME_OWNER_KIND
PROMPT_VERSION = "hint_outcome.v1"
LEDGER_TASK = "hint_outcome"
CLAIM_TASK = "hint_outcome_placement"
VERDICTS = ("reached", "not_reached", "unknown")
#: The answer the call places, clipped (a prompt-size bound only).
ANSWER_CHARS = 6_000
#: One placement's paid-call bounds (the ask, the re-ask, a retry of each):
#: runaway-loop bounds, not money (money is the maps' daily envelope).
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=2, max_calls=4, max_total_tokens=120_000)
#: Whether the answer's node is past a hint's target is read on the route the
#: answer follows; a target elsewhere cannot be compared (no imputation).
_INSTRUCTIONS = (
    "Place the learner's submitted answer on the question's approach map. Name the one route of the map the "
    "answer follows (route_id, or \"\" when it follows none), the LAST node of that route the answer's own work "
    "reaches or establishes (reached_node_id; \"\" when it reaches none beyond the givens), and quote the "
    "answer's words that reach that node (quote, verbatim; \"\" when nothing is reached). Judge only what the "
    "written answer establishes, correct or not later on: a node is reached when its recognizers are met by "
    "the answer's work. Never grade the answer and never use what the hints said."
)


class OutcomePlacementV1(WireModel):
    """Where a submitted answer stands on the item's map (strict)."""

    route_id: str
    reached_node_id: str
    quote: str
    work_matches_a_route: bool


@dataclass
class OutcomeResult:
    """What one placement did. ``status``: placed | not_due | disabled |
    already_placed | no_map | map_changed | busy | stale | capped | unpriced |
    unavailable | failed | invalid."""

    status: str
    attempt_id: str
    reason: str | None = None
    verdicts: dict[str, str] = field(default_factory=dict)
    placement: dict[str, Any] | None = None
    model: str | None = None
    rounds: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, {}, [])}


def placement_enabled(config: Any) -> bool:
    hints = config.hints
    return bool(hints.outcome_placement_enabled and hints.adaptive_enabled and hints.telemetry_enabled
                and hints.maps.enabled)


def env_off() -> bool:
    """The test suite's and a vault copy's guard (no real client without an injected one)."""

    return os.environ.get(maps.BUILDS_ENV, "").strip().lower() == "off" or models_off()


def claim_key(attempt_id: str) -> str:
    return f"hint_outcome:{attempt_id}"


# ---------------------------------------------------------------------------
# What is due
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Due:
    attempt: dict[str, Any]
    hints: list[dict[str, Any]]
    #: The map the answer is placed on: one recorded on the attempt's own
    #: hint rows (fix round 4, F14), or None when none can be used.
    map_record: dict[str, Any] | None
    #: Shown hints judged against no map: their recorded map is not the
    #: placement's, cannot be loaded, or is not the attempt's item revision.
    #: They get a terminal ``unknown`` (reason :data:`MAP_CHANGED`), never a
    #: verdict against another map.
    unplaceable: frozenset[str] = frozenset()


#: The reason of a hint's terminal ``unknown`` when the map it was written on
#: cannot judge it now (fix round 4, F14).
MAP_CHANGED = "map_changed"


def _recorded_map(connection: Any, item: Any, hints: Sequence[Mapping[str, Any]]
                  ) -> tuple[dict[str, Any] | None, frozenset[str]]:
    """The map the hints were written on (fix round 4, F14): the newest
    hint's recorded ``map_id`` that loads, is the item's, and was built for
    the item revision both the hint and today's item are at (so the prompt's
    question is the one the attempt answered). Hints recorded on any other
    map, or on one that fails those checks, are returned as unplaceable.
    Hints with no recorded map name no node, so they are judged as before
    (``no_target``). Never today's map in place of a recorded one."""

    from learnloop.db.stores import approach_maps as map_store
    from learnloop.vault.hashes import practice_item_hash

    current_hash = practice_item_hash(item)

    def usable(hint: Mapping[str, Any]) -> dict[str, Any] | None:
        record = map_store.map_row(connection, str(hint["map_id"]))
        if record is None or str(record.get("practice_item_id")) != item.id:
            return None
        if str(record.get("practice_item_hash")) != current_hash:
            return None
        if hint.get("practice_item_hash") and str(hint["practice_item_hash"]) != current_hash:
            return None
        return record

    chosen: dict[str, Any] | None = None
    for hint in reversed(list(hints)):
        if hint.get("map_id"):
            chosen = usable(hint)
            if chosen is not None:
                break
    unplaceable = frozenset(
        str(hint["id"]) for hint in hints
        if hint.get("map_id") and (chosen is None or str(hint["map_id"]) != str(chosen["id"])))
    return chosen, unplaceable


def _due(vault: LoadedVault, repository: Repository, attempt_id: str) -> tuple[_Due | None, str]:
    """The attempt to place, or why none is due (local reads only)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        attempt = connection.execute(
            "SELECT id, practice_item_id, learner_answer_md, correctness FROM practice_attempts WHERE id = ?",
            (attempt_id,)).fetchone()
        if attempt is None:
            return None, "not_due"
        attempt = dict(attempt)
        correctness = attempt["correctness"]
        if correctness is None or float(correctness) >= 1.0 - 1e-9:
            return None, "not_due"  # ungraded, or fully correct: the grade settles it
        if not str(attempt["learner_answer_md"] or "").strip():
            return None, "not_due"  # an empty answer is at the givens: nothing to place
        hints = [dict(row) for row in connection.execute(
            "SELECT id, hint_kind, level, route_id, from_node_id, target_node_id, map_id, practice_item_hash "
            "FROM help_assists "
            "WHERE attempt_id = ? AND assist_kind = 'hint' AND shown = 1 ORDER BY requested_at, id",
            (attempt_id,)).fetchall()]
        if not hints:
            return None, "not_due"
        placed = connection.execute(
            "SELECT 1 FROM judgment_ledger WHERE task = ? AND right_kind = 'practice_attempt' AND right_id = ? "
            "LIMIT 1", (LEDGER_TASK, attempt_id)).fetchone()
        if placed is not None:
            return None, "already_placed"
        item = vault.practice_items.get(str(attempt["practice_item_id"]))
        if item is None or item.status != "active":
            return None, "not_due"
        if not maps.maps_enabled(vault.config):
            return None, "no_map"
        # F14: the map the hints were written on, never today's in its place.
        recorded, unplaceable = _recorded_map(connection, item, hints)
    if recorded is None and not unplaceable:
        return None, "no_map"  # no hint names a map: nothing to judge against
    return _Due(attempt, hints, recorded, unplaceable), "due"


# ---------------------------------------------------------------------------
# The judgment in code
# ---------------------------------------------------------------------------

def _routes(map_payload: Mapping[str, Any]) -> dict[str, list[str]]:
    return {str(route.get("id")): [str(node) for node in route.get("path") or ()]
            for route in map_payload.get("routes") or ()}


def validate_placement(answer: OutcomePlacementV1, map_payload: Mapping[str, Any], answer_md: str) -> list[str]:
    """Why a placement cannot be used (empty: usable). The node and route
    must be the map's, the node on the route, and the quote the answer's own."""

    reasons: list[str] = []
    routes = _routes(map_payload)
    nodes = {str(node.get("id")) for node in map_payload.get("nodes") or ()}
    if answer.route_id and answer.route_id not in routes:
        reasons.append("unknown_route")
    if answer.reached_node_id and answer.reached_node_id not in nodes:
        reasons.append("unknown_node")
    if answer.route_id in routes and answer.reached_node_id and answer.reached_node_id not in routes[answer.route_id]:
        reasons.append("node_not_on_route")
    if answer.reached_node_id and not answer.quote.strip():
        reasons.append("no_quote")
    if answer.quote.strip() and " ".join(answer.quote.split()) not in " ".join(answer_md.split()):
        reasons.append("quote_not_in_answer")
    return reasons


def hint_verdict(hint: Mapping[str, Any], answer: OutcomePlacementV1, map_payload: Mapping[str, Any]
                 ) -> tuple[str, str | None, str | None]:
    """``(verdict, reason, target)`` for one shown hint (§6.1's "reaches the
    hint's target node, or, for kinds without one, the next node")."""

    routes = _routes(map_payload)
    target = str(hint.get("target_node_id") or "")
    if not target:
        start, route = str(hint.get("from_node_id") or ""), routes.get(str(hint.get("route_id") or ""))
        if start and route and start in route and route.index(start) + 1 < len(route):
            target = route[route.index(start) + 1]
    if not target:
        return "unknown", "no_target", None
    if not answer.route_id or answer.route_id not in routes:
        return "unknown", "answer_on_no_route", target
    path = routes[answer.route_id]
    if target not in path:
        return "unknown", "target_on_another_route", target
    reached = answer.reached_node_id
    if not reached:
        return "not_reached", None, target
    return ("reached" if path.index(target) <= path.index(reached) else "not_reached"), None, target


# ---------------------------------------------------------------------------
# The paid call
# ---------------------------------------------------------------------------

def build_prompt(item: Any, map_payload: Mapping[str, Any], answer_md: str,
                 feedback: Mapping[str, Any] | None = None) -> str:
    nodes = [{"id": node.get("id"), "label": node.get("label"), "state": node.get("state"),
              "recognizers": node.get("recognizers"), "role": node.get("role")}
             for node in map_payload.get("nodes") or ()]
    routes = [{"id": route.get("id"), "name": route.get("name"), "path": route.get("path")}
              for route in map_payload.get("routes") or ()]
    payload: dict[str, Any] = {"task": _INSTRUCTIONS, "question": item.prompt,
                               "approach_map": {"nodes": nodes, "routes": routes},
                               "learner_answer": answer_md[:ANSWER_CHARS]}
    if feedback:
        payload["previous_answer_problems"] = dict(feedback)
    return render_structured_prompt("learnloop hint outcome placement", PROMPT_VERSION, payload)


def place_outcome(vault: LoadedVault, repository: Repository, attempt_id: str, *, client: Any | None = None,
                  clock: Clock | None = None, fence: "maps.BuildFence | None" = None) -> OutcomeResult:
    """Place one hinted attempt's final answer (§6.1) and write the verdicts.
    Measurement only; returns what it did and never raises for a model or
    spend failure."""

    result = OutcomeResult(status="disabled", attempt_id=attempt_id)
    if not placement_enabled(vault.config):
        return result
    due, why = _due(vault, repository, attempt_id)
    if due is None:
        result.status = why
        return result
    item = vault.practice_items[str(due.attempt["practice_item_id"])]
    with maps._claimed(repository, attempt_id, 0.0, fence=fence, key=claim_key(attempt_id), task=CLAIM_TASK,
                       producer=OWNER_KIND) as claim:
        if claim is None:
            result.status = "stale" if fence is not None and not fence.live() else "busy"
            return result
        # Read again under the claim: another process may have placed it.
        due, why = _due(vault, repository, attempt_id)
        if due is None:
            result.status = why
            return result
        if due.map_record is None:
            # F14: no hint's map can judge it now: terminal unknowns, no call.
            _write(repository, due, None, "", model="", clock=clock, claim=claim, invalid=None, result=result)
            result.status, result.reason = "map_changed", MAP_CHANGED
            return result
        return _place_claimed(vault, repository, item, due, claim, result, client=client, clock=clock)


def _place_claimed(vault: LoadedVault, repository: Repository, item: Any, due: _Due, claim: Any,
                   result: OutcomeResult, *, client: Any | None, clock: Clock | None) -> OutcomeResult:
    route = plan_route(vault, ROUTE_TASK, client)  # type: ignore[arg-type]
    subscription = route.billing == "subscription"
    price = vault.config.hints.price_per_million
    answer_md = str(due.attempt["learner_answer_md"] or "")
    map_payload = (due.map_record or {})["map"]
    try:
        resolved = client
        if resolved is None:
            resolved, problem = resolve_client(vault, route)
            if resolved is None:
                result.status, result.reason = "unavailable", problem or "no client"
                return result
        if not subscription and price is None:
            result.status, result.reason = "unpriced", "a metered hint_outcome route needs hints.price_per_million"
            return result
        envelope = maps.maps_envelope(vault, repository, clock=clock)
        if not subscription and envelope.remaining() <= 0:
            result.status, result.reason = "capped", f"{maps.ENVELOPE}: today's metered budget is spent"
            return result

        def admit(_estimate: Any) -> None:
            maps._require_live(repository, claim)

        calls = PaidCalls(route=route, budget=SpendBudget(SpendCaps(max_estimated_usd=None, **_CAPS),
                                                          subscription=subscription),
                          price_per_million=price, repository=maps._FencedRepository(repository, claim),
                          owner_kind=OWNER_KIND, owner_id=str(due.attempt["id"]), admit=admit)
        feedback: dict[str, Any] | None = None
        answer: OutcomePlacementV1 | None = None
        prompt = ""
        for round_ in (1, 2):
            maps._require_live(repository, claim)
            prompt = build_prompt(item, map_payload, answer_md, feedback)
            with spend_envelopes(envelope):
                answer = calls.call(resolved, purpose=PURPOSE, prompt=prompt, result_model=OutcomePlacementV1,
                                    output_tokens=route.output_tokens,
                                    metadata={"attempt_id": due.attempt["id"], "round": round_,
                                              "prompt_version": PROMPT_VERSION})
            result.rounds = round_
            reasons = validate_placement(answer, map_payload, answer_md)
            if not reasons:
                break
            if round_ == 2:
                answer = None
                feedback = {"reasons": reasons}
                break
            feedback = {"reasons": reasons, "previous_answer": answer.model_dump(mode="json")}
        result.model = calls.last_resolved_model or getattr(resolved, "model", None) or route.model
        _write(repository, due, answer, prompt, model=str(result.model or "unknown"), clock=clock, claim=claim,
               invalid=(feedback or {}).get("reasons") if answer is None else None, result=result)
        result.status = "placed" if answer is not None else "invalid"
        result.placement = answer.model_dump(mode="json") if answer is not None else None
        return result
    except maps._LeaseLost as exc:
        result.status, result.reason = "stale", str(exc)
    except SpendLimitExceeded as exc:
        result.status, result.reason = "capped", str(exc)
    except AIInterrupted:
        raise
    except (AIProviderUnavailable, AIInvalidOutput, TimeoutError) as exc:
        result.status, result.reason = "failed", f"{type(exc).__name__}: {exc}"[:300]
    return result


def _write(repository: Repository, due: _Due, answer: OutcomePlacementV1 | None, prompt: str, *, model: str,
           clock: Clock | None, claim: Any, invalid: Sequence[str] | None, result: OutcomeResult) -> None:
    """One verdict per shown hint row, fenced like a map's writes."""

    placement = answer.model_dump(mode="json") if answer is not None else None
    map_record = due.map_record or {}
    # No call was made (F14: no usable map): the verdicts are code's alone.
    called = due.map_record is not None
    with maps._fenced_txn(repository, claim) as connection:
        for hint in due.hints:
            if str(hint["id"]) in due.unplaceable:
                verdict, reason, target = "unknown", MAP_CHANGED, hint.get("target_node_id")
            elif answer is None:
                verdict, reason, target = "unknown", "placement_invalid", hint.get("target_node_id")
            else:
                verdict, reason, target = hint_verdict(hint, answer, map_record["map"])
            result.verdicts[str(hint["id"])] = verdict
            rationale = {"placement": placement, "reason": reason, "invalid": list(invalid or ()) or None,
                         "target_node_id": target, "hint_kind": hint.get("hint_kind"), "level": hint.get("level"),
                         "hint_route_id": hint.get("route_id"), "map_id": map_record.get("id"),
                         "map_version": map_record.get("version"), "hint_map_id": hint.get("map_id"),
                         "rounds": result.rounds, "measurement_only": True}
            append_judgment(connection, task=LEDGER_TASK, left_kind="help_assist", left_id=str(hint["id"]),
                            right_kind="practice_attempt", right_id=str(due.attempt["id"]),
                            judge="llm" if called else "verifier", judge_model=model if called else None,
                            prompt_version=PROMPT_VERSION,
                            input_hash=content_key(prompt or json.dumps(rationale, sort_keys=True, default=str)),
                            verdict=verdict, rationale=json.dumps(rationale, sort_keys=True, default=str),
                            created_at=utc_now_iso(clock))


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

_INFLIGHT: set[tuple[str, str]] = set()
_INFLIGHT_GUARD = threading.Lock()


def _hinted(sqlite_path: Any, attempt_id: str) -> bool:
    """The attempt has a shown hint and no placement yet (a cheap read before
    any thread: a retry answered from its receipt asks again, review F5)."""

    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        if connection.execute(
                "SELECT 1 FROM help_assists WHERE attempt_id = ? AND assist_kind = 'hint' AND shown = 1 LIMIT 1",
                (attempt_id,)).fetchone() is None:
            return False
        return connection.execute(
            "SELECT 1 FROM judgment_ledger WHERE task = ? AND right_kind = 'practice_attempt' AND right_id = ? "
            "LIMIT 1", (LEDGER_TASK, attempt_id)).fetchone() is None


def schedule_outcome_placement(vault: LoadedVault, sqlite_path: Any, attempt_id: str, *, client: Any | None = None,
                               clock: Clock | None = None, builds: "maps.BackgroundBuilds | None" = None,
                               on_done: Callable[[OutcomeResult], None] | None = None) -> threading.Thread | None:
    """Start outcome placement for a submitted attempt in the background
    (after the submit's response is built). Returns at once and never raises;
    None when nothing was started (switched off, guarded, not hinted, already
    in flight, or refused by the registry)."""

    key: tuple[str, str] | None = None
    try:
        if not placement_enabled(vault.config):
            return None
        if client is None and env_off():
            return None
        if not _hinted(sqlite_path, attempt_id):
            return None
        registry = builds if builds is not None else maps._DEFAULT_BUILDS
        candidate = (str(Path(sqlite_path)), attempt_id)
        with _INFLIGHT_GUARD:
            if candidate in _INFLIGHT:
                return None
            _INFLIGHT.add(candidate)
            key = candidate

        def work(fence: "maps.BuildFence") -> Callable[[], None]:
            def run() -> None:
                try:
                    if not fence.live():
                        return
                    repository = Repository.attach(Path(sqlite_path))
                    outcome = place_outcome(vault, repository, attempt_id, client=client, clock=clock, fence=fence)
                    LOG.info("hint outcome placement: %s", json.dumps(outcome.as_dict(), sort_keys=True, default=str))
                    if on_done is not None:
                        on_done(outcome)
                except Exception:  # noqa: BLE001 - measurement never reaches the submit
                    LOG.warning("hint outcome placement failed", exc_info=True)
                finally:
                    with _INFLIGHT_GUARD:
                        _INFLIGHT.discard(candidate)

            return run

        thread = registry.launch(sqlite_path, work, name=f"learnloop-hint-outcome-{attempt_id}")
        if thread is None:
            return None
        key = None
        with maps._INFLIGHT_GUARD:
            maps._THREADS[:] = [existing for existing in maps._THREADS if existing.is_alive()] + [thread]
        return thread
    except Exception:  # noqa: BLE001 - scheduling never fails a submit
        LOG.warning("hint outcome scheduling failed", exc_info=True)
        return None
    finally:
        if key is not None:
            with _INFLIGHT_GUARD:
                _INFLIGHT.discard(key)


# ---------------------------------------------------------------------------
# Reconciliation (H2b review F5)
# ---------------------------------------------------------------------------

#: The hinted attempts a vault's open looks back over, and how many it
#: places in one pass: runaway bounds on a backlog, not money (each placement
#: still joins the maps' envelope, and a checkpointed answer is not paid again).
RECONCILE_LOOKBACK_DAYS = 14
RECONCILE_LIMIT = 20
#: How many candidates one read of the backlog returns (re-review F8): the
#: pass reads page after page, past candidates it cannot place, so the bound
#: above counts placements, never candidates looked at.
RECONCILE_PAGE = 50
#: Outcomes that placed nothing and spent nothing: the pass moves on to the
#: next candidate without counting them against :data:`RECONCILE_LIMIT`.
_NOTHING_PLACED = frozenset({"not_due", "no_map", "already_placed", "busy", "disabled", "map_changed"})
#: An interrupted placement (fix round 4, F13): the pass stops at once.
_INTERRUPTED = "interrupted"
#: Outcomes after which the rest waits for the next open (or the envelope's next day).
_STOP = frozenset({"capped", "unpriced", "unavailable", "stale", _INTERRUPTED})


def _unplaced_page(sqlite_path: Any, *, since: str, limit: int,
                   after: tuple[str, str] | None = None) -> list[tuple[str, str]]:
    """One page of :func:`unplaced_attempts` as ``(created_at, id)``, after
    the cursor ``after`` (the last candidate of the previous page)."""

    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not {"help_assists", "judgment_ledger", "practice_attempts"} <= tables:
            return []
        cursor_sql, cursor_values = "", ()
        if after is not None:
            cursor_sql = "AND (a.created_at > ? OR (a.created_at = ? AND a.id > ?)) "
            cursor_values = (after[0], after[0], after[1])
        rows = connection.execute(
            "SELECT a.created_at, a.id FROM practice_attempts a WHERE a.created_at >= ? "
            "AND a.correctness IS NOT NULL "
            "AND a.correctness < 1.0 - 1e-9 AND TRIM(COALESCE(a.learner_answer_md, '')) != '' "
            "AND EXISTS (SELECT 1 FROM help_assists h WHERE h.attempt_id = a.id AND h.assist_kind = 'hint' "
            "AND h.shown = 1) "
            "AND NOT EXISTS (SELECT 1 FROM judgment_ledger j WHERE j.task = ? AND j.right_kind = 'practice_attempt' "
            f"AND j.right_id = a.id) {cursor_sql}ORDER BY a.created_at, a.id LIMIT ?",
            (since, LEDGER_TASK, *cursor_values, int(limit))).fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]


def unplaced_attempts(sqlite_path: Any, *, since: str, limit: int = RECONCILE_LIMIT) -> list[str]:
    """Hinted attempts submitted since ``since``, graded not fully correct
    with an answer, and never placed: the work a process that ended (or a
    vault switch that fenced it) left undone. Oldest first; local reads only.
    :func:`_due` decides each one again under its claim."""

    return [attempt_id for _created, attempt_id in _unplaced_page(sqlite_path, since=since, limit=limit)]


def reconcile_outcome_placements(vault: LoadedVault, sqlite_path: Any, *, client: Any | None = None,
                                 clock: Clock | None = None, builds: "maps.BackgroundBuilds | None" = None,
                                 limit: int = RECONCILE_LIMIT,
                                 on_done: Callable[[OutcomeResult], None] | None = None) -> threading.Thread | None:
    """At a vault's open: place, one after another in ONE background thread,
    the hinted attempts of the last :data:`RECONCILE_LOOKBACK_DAYS` days that
    were never placed (outcome work is launched in memory after a submit, so
    a process that ended first, a vault switch that fenced it, or a receipt
    recovery left it undone). Every placement goes through
    :func:`place_outcome`: the same switches, claim, lease, fence and
    envelope, and a paid answer checkpointed before the interruption is
    recovered without paying again. The candidates are read page by page,
    oldest first, past those that place nothing (an inactive item, no map:
    re-review F8), so they never hold a later one out of the pass; ``limit``
    bounds the placements. One pass per vault at a time. Returns at once and
    never raises; None when nothing was started."""

    try:
        if not placement_enabled(vault.config):
            return None
        if client is None and env_off():
            return None
        from datetime import timedelta

        from learnloop.clock import parse_utc

        since = (parse_utc(utc_now_iso(clock)) - timedelta(days=RECONCILE_LOOKBACK_DAYS)).isoformat().replace(
            "+00:00", "Z")
        page_size = max(1, int(RECONCILE_PAGE))
        first_page = _unplaced_page(sqlite_path, since=since, limit=page_size)
        if not first_page:
            return None
        registry = builds if builds is not None else maps._DEFAULT_BUILDS
        path = str(Path(sqlite_path))
        pass_key = (path, _PASS)
        with _INFLIGHT_GUARD:
            if pass_key in _INFLIGHT:
                return None
            _INFLIGHT.add(pass_key)

        def place_one(repository: Repository, attempt_id: str, fence: "maps.BuildFence") -> OutcomeResult | None:
            candidate = (path, attempt_id)
            with _INFLIGHT_GUARD:
                if candidate in _INFLIGHT:
                    return None  # a submit's own placement has it
                _INFLIGHT.add(candidate)
            try:
                return place_outcome(vault, repository, attempt_id, client=client, clock=clock, fence=fence)
            except AIInterrupted as exc:
                # Fix round 4, F13: an interrupted turn stops the pass at once
                # (a shutdown or a cancel, never a reason to try the next).
                return OutcomeResult(status=_INTERRUPTED, attempt_id=attempt_id, reason=str(exc)[:300])
            except Exception as exc:  # noqa: BLE001 - one attempt never stops the pass
                # F13: the skips decided before any call are statuses, never
                # exceptions, so a failure here may follow a model call: it
                # counts against the pass's bound (conservatively, also one
                # raised before a call could start).
                LOG.warning("hint outcome reconciliation failed for %s", attempt_id, exc_info=True)
                return OutcomeResult(status="failed", attempt_id=attempt_id,
                                     reason=f"{type(exc).__name__}: {exc}"[:300])
            finally:
                with _INFLIGHT_GUARD:
                    _INFLIGHT.discard(candidate)

        def work(fence: "maps.BuildFence") -> Callable[[], None]:
            def run() -> None:
                try:
                    repository = Repository.attach(Path(sqlite_path))
                    placed, page = 0, first_page
                    while page:
                        for _created, attempt_id in page:
                            if not fence.live() or placed >= limit:
                                return
                            outcome = place_one(repository, attempt_id, fence)
                            if outcome is None:
                                continue
                            LOG.info("hint outcome placement (reconciled): %s",
                                     json.dumps(outcome.as_dict(), sort_keys=True, default=str))
                            if on_done is not None:
                                on_done(outcome)
                            if outcome.status in _STOP:
                                return  # the rest waits for the next open (or the envelope's next day)
                            if outcome.status not in _NOTHING_PLACED:
                                placed += 1
                        page = _unplaced_page(sqlite_path, since=since, limit=page_size, after=page[-1])
                finally:
                    with _INFLIGHT_GUARD:
                        _INFLIGHT.discard(pass_key)

            return run

        try:
            thread = registry.launch(sqlite_path, work, name="learnloop-hint-outcome-reconcile")
        except BaseException:
            thread = None
            raise
        finally:
            if thread is None:
                with _INFLIGHT_GUARD:
                    _INFLIGHT.discard(pass_key)
        if thread is None:
            return None
        with maps._INFLIGHT_GUARD:
            maps._THREADS[:] = [existing for existing in maps._THREADS if existing.is_alive()] + [thread]
        return thread
    except Exception:  # noqa: BLE001 - reconciliation never blocks opening a vault
        LOG.warning("hint outcome reconciliation failed", exc_info=True)
        return None


#: The in-flight key of a vault's reconciliation pass (one at a time).
_PASS = "__reconcile_outcome_placements__"


__all__ = [
    "LEDGER_TASK", "OWNER_KIND", "OutcomePlacementV1", "OutcomeResult", "PROMPT_VERSION", "RECONCILE_LIMIT",
    "RECONCILE_LOOKBACK_DAYS", "RECONCILE_PAGE", "ROUTE_TASK", "VERDICTS", "hint_verdict", "place_outcome", "placement_enabled",
    "reconcile_outcome_placements", "schedule_outcome_placement", "unplaced_attempts", "validate_placement",
]
