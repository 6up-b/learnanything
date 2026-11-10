"""Reader RW5d P5: the prefetch ledger's reads (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §10b.6, §13.2b).

The decision model (:mod:`.prefetch_model`) is recomputed from the ledger at
decision time; this module reads what it needs, by SQL, from a connection:

* the closed, built decisions (``figure_prefetch_decisions`` with an outcome
  ``opened`` or ``neither`` and a request) in time order: the opening model's
  observations; ``asked`` rows are demand without the cue, reported, never
  used in the decision (R11);
* the plan days (``model_call_receipts`` on a plan provider, by local day:
  requests and known tokens) and the pauses (``plan_usage_pauses``): the
  pause-risk model's data, and the foreground minutes pauses blocked
  (pressed calls that failed inside a pause window, times the measured call
  latency);
* the measured pressed build latencies by tier and the tier mixes (W_tier).

Whose call a receipt was (:func:`call_build_modes`, :func:`background_call`):
no receipt says it (a pre-build's figure calls carry a press's owner kind), so
the build mode is read from the stored figure the receipt's owner names. Under
``prefetch_decision_v1`` the ``owner_kind`` filters meant to leave the
pre-builder's calls out never matched, so W and the blocked minutes read every
call; ``prefetch_decision_v2`` (mvp-0.58, :func:`pressed_waits_on`) reads the
quick tiers' W from pressed calls with the other calls as a prior and the
blocked minutes from foreground calls only.

:func:`report_block` is ``learnloop reader report``'s ``prefetch`` block:
decisions and outcomes by trigger, the posteriors' contraction, the measured
waits, the pauses with and without prebuilds before them, and the builds
skipped for power and caps and those resumed after waiting. Counts and
posteriors only, never learner text.
Read-only; a vault before migration 237 reads as empty.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.figures import prefetch_model as PM

DECISIONS_TABLE = "figure_prefetch_decisions"
PAUSES_TABLE = "plan_usage_pauses"
#: Decisions whose Thompson draw said build: ``build``, and the temporary deferrals (the power, the
#: plan, today's caps), retried while their horizon is open (Codex review F5; a cap since follow-ups
#: batch 7 (A), rechecked before any request). Once built, any of them is an observation of opening
#: (the draw built it and the cue was there).
BUILD_DECISIONS = ("build", "deferred_power", "deferred_plan", "capped")
#: The report's names for the deferrals, a decision's verdict to its key under ``skipped``/``resumed``.
DEFERRALS = {"deferred_power": "power", "deferred_plan": "plan", "capped": "caps"}


def plan_providers(vault: Any) -> set[str]:
    """The vault's plan profiles (subscription billing): whose receipts are the plan's load."""

    from learnloop.practice_index.paid import billing_for

    return {name for name, profile in vault.config.ai.providers.items()
            if billing_for(getattr(profile, "type", None)) == "subscription"}


def pressed_waits_on(vault: Any) -> bool:
    """The figure wait estimate's successor (``FIGURE_WAIT_VERSIONS``) with its switch
    ``figures.prefetch.pressed_waits`` on: decisions read ``prefetch_decision_v2`` (:func:`load_model`)."""

    from learnloop.algorithm_versions import FIGURE_WAIT_VERSIONS

    config = vault.config
    return (getattr(config.algorithms, "algorithm_version", None) in FIGURE_WAIT_VERSIONS
            and bool(config.figures.prefetch.pressed_waits))


def has_tables(connection: Any) -> bool:
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?)", (DECISIONS_TABLE, PAUSES_TABLE))}
    return names == {DECISIONS_TABLE, PAUSES_TABLE}


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _when(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _minutes(start: Any, end: Any) -> float | None:
    begun, done = _when(start), _when(end)
    if begun is None or done is None:
        return None
    return max(0.0, (done - begun).total_seconds() / 60.0)


def _dicts(cursor: Any) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def decisions(connection: Any) -> list[dict[str, Any]]:
    if not _table(connection, DECISIONS_TABLE):
        return []
    return _dicts(connection.execute(f"SELECT * FROM {DECISIONS_TABLE} ORDER BY created_at, id"))


def observations(rows: Iterable[Mapping[str, Any]]) -> list[PM.Observation]:
    """The opening model's data: built rows closed ``opened`` or ``neither`` (time order)."""

    return [PM.Observation(str(row["trigger_kind"]), row.get("source_key"), row.get("p_open_content"),
                           row.get("outcome") == "opened")
            for row in rows
            if row.get("decision") in BUILD_DECISIONS and row.get("request_id")
            and row.get("outcome") in ("opened", "neither")]


# -- the plan's load and pauses ---------------------------------------------------------------------------

def _local_day(value: Any, offset: timedelta) -> str | None:
    when = _when(value)
    return None if when is None else (when + offset).date().isoformat()


def plan_receipts(connection: Any, plan_providers: Iterable[str]) -> list[dict[str, Any]]:
    providers = sorted({str(name) for name in plan_providers if name})
    if not providers or not _table(connection, "model_call_receipts"):
        return []
    marks = ",".join("?" for _ in providers)
    return _dicts(connection.execute(
        "SELECT owner_kind, owner_id, purpose, provider, status, started_at, finished_at, input_tokens, output_tokens "
        f"FROM model_call_receipts WHERE provider IN ({marks}) ORDER BY started_at", providers))


# -- whose call a receipt was: a press's or the pre-builder's ------------------------------------------

#: The figure calls' receipt purposes (``model_call_receipts.purpose``, the route's task).
AUTHOR_PURPOSE = "figure_author"
RICH_AUTHOR_PURPOSE = "figure_rich_author"
#: The prefetch judge runs in the background only (spec §10b.2): every call of it is the pre-builder's.
JUDGE_PURPOSE = "figure_prefetch_judge"


def call_build_modes(connection: Any) -> dict[str, str]:
    """``owner_id`` -> the build mode (``pressed`` or ``prefetch``) of the build whose figure calls
    carry it, read from what the ledger records (no receipt says it: a pre-build's calls have the
    same owner kind as a press's).

    The figure author's receipts are owned by ``figure:<content_key(input_hash, generation)>``
    (``service.build_figure``), the generation being how many figures of that input were stored
    before the build (``store.builds_for_input`` over ``service.ALL_SPEC_VERSIONS``); the rich
    author's by ``figure_rich:<rich.content_key_for(payload)>`` (the input, the quick figure it
    follows, the quick build's generation). So each stored figure names its build's owner, and its
    building request (``interactive_figures.request_id``, never a later reuse's row) the mode; a
    figure older than the request ledger is a press's. A build that stored nothing (refused, or
    crashed before its row) shares its owner with the next build of that input, when there is
    one; otherwise its receipts are unowned here (:func:`background_call` reads them as foreground).
    """

    if not _table(connection, "interactive_figures") or not _table(connection, "figure_requests"):
        return {}
    from learnloop.ai.execution import content_key
    from learnloop.figures.service import ALL_SPEC_VERSIONS

    marks = ",".join("?" for _ in ALL_SPEC_VERSIONS)
    rows = _dicts(connection.execute(
        "SELECT f.id, f.input_hash, f.fuller_of_id, f.origin, f.tier, r.build_mode FROM interactive_figures f "
        "LEFT JOIN figure_requests r ON r.id = f.request_id "
        f"WHERE f.input_hash IS NOT NULL AND f.spec_version IN ({marks}) ORDER BY f.created_at, f.id",
        tuple(ALL_SPEC_VERSIONS)))
    generation: dict[str, int] = {}
    seen: Counter[str] = Counter()
    modes: dict[str, str] = {}
    for row in rows:
        generation[str(row["id"])] = seen[str(row["input_hash"])]
        seen[str(row["input_hash"])] += 1
    for row in rows:
        mode = str(row["build_mode"] or ("prefetch" if row["origin"] == "prefetch" else "pressed"))
        follows = row["fuller_of_id"]
        built_at = generation.get(str(follows), generation[str(row["id"])]) if follows else generation[str(row["id"])]
        if not follows:
            # A quick figure, or a rich-only build's figure: the author's call that chose it.
            modes.setdefault(f"figure:{content_key({'input_hash': row['input_hash'], 'generation': built_at})}", mode)
        if row["tier"] in PM.RICH_TIERS:
            rich = content_key({"input_hash": row["input_hash"], "fuller_of": follows, "generation": built_at})
            modes.setdefault(f"figure_rich:{rich}", mode)
    return modes


def background_call(row: Mapping[str, Any], modes: Mapping[str, str]) -> bool:
    """Whether a receipt is the pre-builder's own background call (``prefetch_decision_v2``): the
    judge's, or a figure author's or rich author's call whose build was a pre-build
    (:func:`call_build_modes`). Any other call, an unowned figure call included, is foreground."""

    purpose = row.get("purpose")
    if purpose == JUDGE_PURPOSE:
        return True
    return purpose in (AUTHOR_PURPOSE, RICH_AUTHOR_PURPOSE) and modes.get(str(row.get("owner_id"))) == "prefetch"


def _tokens(row: Mapping[str, Any]) -> int | None:
    """A receipt's reported tokens, or None when the provider reported none (missing, not zero)."""

    if row.get("input_tokens") is None and row.get("output_tokens") is None:
        return None
    return int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)


def day_load(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta = timedelta(0)
             ) -> tuple[int, int]:
    """``(requests, known tokens)`` on a plan provider during one local day."""

    found = plan_day(connection, plan_providers, day, offset=offset)
    return found.requests, found.tokens


def plan_day(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta = timedelta(0),
             paused: bool = False) -> PM.PlanDay:
    """One local day's plan load: its requests, its known tokens and how many requests reported them."""

    requests = tokens = reported = 0
    for row in plan_receipts(connection, plan_providers):
        if _local_day(row["started_at"], offset) == day:
            requests += 1
            if (known := _tokens(row)) is not None:
                reported += 1
                tokens += known
    return PM.PlanDay(requests, tokens, paused, reported)


def pauses(connection: Any) -> list[dict[str, Any]]:
    if not _table(connection, PAUSES_TABLE):
        return []
    return _dicts(connection.execute(f"SELECT * FROM {PAUSES_TABLE} ORDER BY hit_at, id"))


def plan_days(connection: Any, plan_providers: Iterable[str], *, today: str,
              offset: timedelta = timedelta(0)) -> list[PM.PlanDay]:
    """Each past local day with plan activity (today excluded: it is still open)."""

    requests: Counter[str] = Counter()
    tokens: Counter[str] = Counter()
    reported: Counter[str] = Counter()
    for row in plan_receipts(connection, plan_providers):
        day = _local_day(row["started_at"], offset)
        if day is None or day >= today:
            continue
        requests[day] += 1
        if (known := _tokens(row)) is not None:
            reported[day] += 1
            tokens[day] += known
    paused = {day for row in pauses(connection) if (day := _local_day(row["hit_at"], offset))}
    return [PM.PlanDay(requests[day], tokens[day], day in paused, reported[day])
            for day in sorted(set(requests) | (paused - {today})) if day < today]


def blocked_minutes(connection: Any, plan_providers: Iterable[str], *, pressed_only: bool = False) -> float | None:
    """Measured foreground minutes a pause blocked, per pause: the pressed (non-background) plan
    calls that failed inside a pause's window, times the mean measured plan call latency. None
    with no pause or no measured latency. ``pressed_only`` (``prefetch_decision_v2``,
    :func:`blocked_basis`) leaves the pre-builder's own calls out of both."""

    return blocked_basis(connection, plan_providers, pressed_only=pressed_only)["minutes"]


def blocked_basis(connection: Any, plan_providers: Iterable[str], *, pressed_only: bool = False) -> dict[str, Any]:
    """:func:`blocked_minutes` and what it counted: ``minutes`` (None: no pause or no measured
    latency), ``refused`` (failed calls inside a pause window it counted), ``background_left_out``
    (the pre-builder's own failed calls inside one, :func:`background_call`), ``latency_calls`` and
    ``pauses``. Without ``pressed_only`` (``prefetch_decision_v1``) every call counts: its owner-kind
    filter never matched a receipt (no figure call's owner kind starts with ``prefetch``)."""

    found: dict[str, Any] = {"minutes": None, "refused": 0, "background_left_out": 0, "latency_calls": 0,
                             "pauses": 0}
    windows = [(_when(row["hit_at"]), _when(row.get("reset_at"))) for row in pauses(connection)]
    windows = [(start, end) for start, end in windows if start is not None and end is not None]
    found["pauses"] = len(windows)
    if not windows:
        return found
    receipts = plan_receipts(connection, plan_providers)
    modes = call_build_modes(connection) if pressed_only else {}

    def background(row: Mapping[str, Any]) -> bool:
        if pressed_only:
            return background_call(row, modes)
        return str(row.get("owner_kind") or "").startswith("prefetch")

    durations = [value for row in receipts if row["status"] == "completed" and not (pressed_only and background(row))
                 and (value := _minutes(row["started_at"], row.get("finished_at"))) is not None and value > 0]
    found["latency_calls"] = len(durations)
    if not durations:
        return found
    latency = sum(durations) / len(durations)
    refused = left_out = 0
    for row in receipts:
        if row["status"] != "failed":
            continue
        when = _when(row["started_at"])
        if when is None or not any(start <= when <= end for start, end in windows):
            continue
        if background(row):
            left_out += 1
        else:
            refused += 1
    found.update(minutes=refused * latency / len(windows), refused=refused, background_left_out=left_out)
    return found


# -- W_tier --------------------------------------------------------------------------------------------

def _figures_by_request(connection: Any) -> dict[str, list[dict[str, Any]]]:
    if not _table(connection, "figure_requests") or not _table(connection, "interactive_figures"):
        return {}
    found: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _dicts(connection.execute(
            "SELECT r.id AS request_id, r.build_mode, r.prefetch_decision_id, r.created_at AS requested_at, "
            "f.id AS figure_id, f.tier, f.fuller_of_id, f.created_at, f.input_hash "
            "FROM figure_requests r JOIN interactive_figures f ON f.request_id = r.id OR f.id = r.figure_id "
            "ORDER BY f.created_at, f.id")):
        found[str(row["request_id"])].append(row)
    return found


def _waited_tier(rows: list[dict[str, Any]]) -> str | None:
    """The tier a request's learner waited for: its rich figure's when one followed, else its own."""

    rich = [row["tier"] for row in rows if row["tier"] in PM.RICH_TIERS]
    if rich:
        return str(rich[-1])
    tiers = [row["tier"] for row in rows if row["tier"]]
    return str(tiers[0]) if tiers else None


def waits(connection: Any, *, pressed_only: bool = False) -> PM.Waits:
    """W_tier's measurements. The rich tiers: pressed requests to their stored rich figures. The quick
    tiers: the figure author's completed calls; ``prefetch_decision_v1`` reads them all alike (its
    ``owner_kind`` filter never matched: no figure call's owner kind starts with ``prefetch``), and
    ``pressed_only`` (``prefetch_decision_v2``) takes the pressed builds' calls as the measurement and
    every other call as its prior (:func:`learnloop.figures.prefetch_model.wait_estimate`)."""

    by_request = _figures_by_request(connection)
    latencies: dict[str, list[float]] = defaultdict(list)
    pressed_tiers: list[str] = []
    for rows in by_request.values():
        if rows[0]["build_mode"] != "pressed":
            continue
        tier = _waited_tier(rows)
        if tier:
            pressed_tiers.append(tier)
        for row in rows:
            if row["tier"] in PM.RICH_TIERS and (value := _minutes(row["requested_at"], row["created_at"])):
                latencies[str(row["tier"])].append(value)
    estimates: dict[str, PM.WaitEstimate] = {}
    if _table(connection, "model_call_receipts") and pressed_only:
        modes = call_build_modes(connection)
        pressed: list[float] = []
        others: list[float] = []
        for owner, start, end in connection.execute(
                "SELECT owner_id, started_at, finished_at FROM model_call_receipts WHERE purpose = ? "
                "AND status = 'completed'", (AUTHOR_PURPOSE,)):
            value = _minutes(start, end)
            if value:
                (pressed if modes.get(str(owner)) == "pressed" else others).append(value)
        estimate = PM.wait_estimate(pressed, others)
        estimates = {tier: estimate for tier in PM.QUICK_TIERS}
    elif _table(connection, "model_call_receipts"):
        # prefetch_decision_v1: the quick tiers: the figure author's measured call duration.
        for row in connection.execute(
                "SELECT started_at, finished_at FROM model_call_receipts WHERE purpose = 'figure_author' "
                "AND status = 'completed' AND owner_kind NOT LIKE 'prefetch%'"):
            value = _minutes(row[0], row[1])
            if value:
                for tier in PM.QUICK_TIERS:
                    latencies[tier].append(value)
    by_kind: dict[str, list[str]] = defaultdict(list)
    kinds = {str(row["id"]): str(row["trigger_kind"]) for row in decisions(connection)}
    for rows in by_request.values():
        decision = rows[0].get("prefetch_decision_id")
        if rows[0]["build_mode"] == "prefetch" and decision in kinds and (tier := _waited_tier(rows)):
            by_kind[kinds[decision]].append(tier)
    return PM.waits(latencies, pressed_tiers, by_kind, estimates)


def incremental(connection: Any) -> PM.Incremental:
    """The measured calls a build makes (Codex review F14): the figure author's calls per authored
    request (its receipts per ``figure:<request>`` owner) and the rich author's per rich job (per
    ``figure_rich:<request>`` owner). Unmeasured: None (the structural minimum, one call)."""

    if not _table(connection, "model_call_receipts"):
        return PM.Incremental()

    def per_owner(purpose: str) -> float | None:
        row = connection.execute(
            "SELECT COUNT(*), COUNT(DISTINCT owner_id) FROM model_call_receipts WHERE purpose = ? "
            "AND status IN ('completed', 'failed') AND owner_id IS NOT NULL", (purpose,)).fetchone()
        return float(row[0]) / float(row[1]) if row and row[1] else None

    return PM.Incremental(per_owner("figure_author"), per_owner("figure_rich_author"))


def load_model(connection: Any, plan_providers: Iterable[str], *, now: datetime,
               offset: timedelta = timedelta(0), pressed_waits: bool = True) -> PM.Model:
    """The decision model from the ledger. ``pressed_waits`` (the figure wait estimate's successor,
    :func:`pressed_waits_on`): W from pressed calls with a prior and the
    blocked minutes from foreground calls (``prefetch_decision_v2``); off, ``prefetch_decision_v1``
    exactly."""

    providers = list(plan_providers)
    today = (now + offset).date().isoformat()
    rows = decisions(connection)
    pause = PM.pause_posterior(plan_days(connection, providers, today=today, offset=offset))
    blocked = blocked_basis(connection, providers, pressed_only=pressed_waits)
    return PM.Model(
        opening=PM.open_posterior(observations(rows)),
        pause=pause,
        waits=waits(connection, pressed_only=pressed_waits),
        blocked_minutes=blocked["minutes"],
        load_today=pause.load(plan_day(connection, providers, today, offset=offset)),
        incremental=incremental(connection),
        version=PM.MODEL_VERSION if pressed_waits else PM.MODEL_VERSION_V1,
        blocked_basis={name: value for name, value in blocked.items() if name != "minutes"} if pressed_waits else None,
    )


# -- the caps ------------------------------------------------------------------------------------------

def started_today(connection: Any, *, today: str, offset: timedelta = timedelta(0)) -> set[str]:
    """The decisions whose build started today (Codex review F6: the cap counts work when it
    starts, a resumed decision of an earlier day included): their prefetch requests stored today."""

    if not _table(connection, "figure_requests"):
        return set()
    return {str(decision) for decision, created_at in connection.execute(
                "SELECT prefetch_decision_id, created_at FROM figure_requests WHERE build_mode = 'prefetch' "
                "AND prefetch_decision_id IS NOT NULL")
            if _local_day(created_at, offset) == today}


def builds_today(connection: Any, *, today: str, offset: timedelta = timedelta(0)) -> int:
    return len(started_today(connection, today=today, offset=offset))


def render_minutes_left(vault: Any, sqlite_path: Any, *, now: datetime | None = None) -> float:
    """``figures.prefetch.max_daily_render_minutes`` less today's background render minutes
    (Codex review F6: the rich worker checks it when a prebuild's rich job starts and before
    each of its requests)."""

    from contextlib import closing

    from learnloop.db.connection import connect

    moment = (now or datetime.now(UTC)).astimezone()
    offset = moment.utcoffset() or timedelta(0)
    today = (moment.astimezone(UTC) + offset).date().isoformat()
    with closing(connect(sqlite_path, read_only=True)) as connection:
        used = render_minutes_today(connection, today=today, offset=offset)
    return float(vault.config.figures.prefetch.max_daily_render_minutes) - used


def capacity_left(vault: Any, sqlite_path: Any, *, now: datetime | None = None) -> bool:
    """Today's ``figures.prefetch`` caps both have room (the durable count of started builds): what
    a pass would admit before it reserves a build. The Reader's "a prebuild is coming" reads this."""

    from contextlib import closing

    from learnloop.db.connection import connect

    moment = (now or datetime.now(UTC)).astimezone()
    offset = moment.utcoffset() or timedelta(0)
    today = (moment.astimezone(UTC) + offset).date().isoformat()
    section = vault.config.figures.prefetch
    with closing(connect(sqlite_path, read_only=True)) as connection:
        return (builds_today(connection, today=today, offset=offset) < int(section.max_daily_builds)
                and render_minutes_today(connection, today=today, offset=offset) < float(section.max_daily_render_minutes))


def render_minutes_today(connection: Any, *, today: str, offset: timedelta = timedelta(0)) -> float:
    """Wall-clock minutes of today's background rich builds (a prebuild's rich figure: its request to its row)."""

    total = 0.0
    for rows in _figures_by_request(connection).values():
        if rows[0]["build_mode"] != "prefetch":
            continue
        for row in rows:
            if row["tier"] in PM.RICH_TIERS and _local_day(row["created_at"], offset) == today:
                total += _minutes(row["requested_at"], row["created_at"]) or 0.0
    return total


# -- the report block ----------------------------------------------------------------------------------

def _built_at(connection: Any, row: Mapping[str, Any]) -> datetime | None:
    """When a decision's build started (its request row), a resumed decision's later than its own
    row; the decision's time when that request can't be read."""

    found = connection.execute("SELECT created_at FROM figure_requests WHERE id = ?",
                               (str(row["request_id"]),)).fetchone() if _table(connection, "figure_requests") else None
    return _when(found[0] if found else None) or _when(row["created_at"])


def report_block(connection: Any, *, since: datetime | None = None,
                 plan_providers: Iterable[str] = (), now: datetime | None = None,
                 pressed_waits: bool = True) -> dict[str, Any]:
    """``learnloop reader report``'s ``prefetch`` block (spec §10b.6), read as the decisions read
    the ledger now (``pressed_waits``, :func:`load_model`)."""

    current = now or datetime.now(UTC)
    rows = [row for row in decisions(connection)
            if since is None or ((when := _when(row["created_at"])) is not None and when >= since)]
    by_trigger: dict[str, Any] = {}
    for kind in PM.TRIGGER_KINDS:
        mine = [row for row in rows if row["trigger_kind"] == kind]
        by_trigger[kind] = {
            "decisions": dict(Counter(str(row["decision"]) for row in mine)),
            "built": sum(1 for row in mine if row["decision"] in BUILD_DECISIONS and row.get("request_id")),
            "outcomes": dict(Counter(str(row["outcome"]) for row in mine if row.get("outcome"))),
            "opened": sum(1 for row in mine if row.get("outcome") == "opened"),
            "asked": sum(1 for row in mine if row.get("outcome") == "asked"),
            "open": sum(1 for row in mine if not row.get("outcome")),
        }
    providers = list(plan_providers)
    model = load_model(connection, providers, now=current, pressed_waits=pressed_waits)
    pause_rows = [row for row in pauses(connection)
                  if since is None or ((when := _when(row["hit_at"])) is not None and when >= since)]
    built_times = [when for row in decisions(connection) if row["decision"] in BUILD_DECISIONS and row.get("request_id")
                   and (when := _built_at(connection, row)) is not None]
    with_prebuilds = 0
    for row in pause_rows:
        hit = _when(row["hit_at"])
        if hit is not None and any(when.date() == hit.date() and when <= hit for when in built_times):
            with_prebuilds += 1
    return {
        "decisions_by_trigger": by_trigger,
        "posterior": {"opening": model.opening.summary(), "pause": model.pause.summary(),
                      "model_version": model.version},
        "measured_wait": model.waits.summary(),
        "blocked_minutes_per_pause": model.blocked_minutes,
        **({"blocked_basis": dict(model.blocked_basis)} if model.blocked_basis is not None else {}),
        "pauses": {"count": len(pause_rows), "with_prebuilds_earlier_that_day": with_prebuilds,
                   "without_prebuilds": len(pause_rows) - with_prebuilds},
        # Follow-ups batch 7 (A): a deferred decision is built later or not at all, so it is one or
        # the other, never both: ``skipped`` has no build (yet), ``resumed`` was built after it waited.
        "skipped": {name: sum(1 for row in rows if row["decision"] == verdict and not row.get("request_id"))
                    for verdict, name in DEFERRALS.items()},
        "resumed": {name: sum(1 for row in rows if row["decision"] == verdict and row.get("request_id"))
                    for verdict, name in DEFERRALS.items()},
        "propensity_mean": (round(sum(float(row["propensity"] or 0) for row in rows) / len(rows), 4)
                            if rows else None),
    }


def add_report_block(report: dict[str, Any], sqlite_path: Any, *, since: str | None = None,
                     plan_providers: Iterable[str] = (), now: datetime | None = None,
                     pressed_waits: bool = True) -> dict[str, Any]:
    """Put :func:`report_block` under the reader report's ``figures`` (``learnloop reader report``
    calls it only with ``figures.prefetch_enabled`` on, so off the report is P2b's)."""

    from contextlib import closing

    from learnloop.db.connection import connect

    with closing(connect(sqlite_path, read_only=True)) as connection:
        block = report_block(connection, since=_when(since) if since else None, plan_providers=plan_providers,
                             now=now, pressed_waits=pressed_waits)
    report.setdefault("figures", {})["prefetch"] = block
    return report


def anchor_of(row: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        value = json.loads(row.get("anchor_json") or "null")
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


__all__ = [
    "AUTHOR_PURPOSE",
    "BUILD_DECISIONS",
    "DECISIONS_TABLE",
    "DEFERRALS",
    "JUDGE_PURPOSE",
    "RICH_AUTHOR_PURPOSE",
    "add_report_block",
    "PAUSES_TABLE",
    "anchor_of",
    "background_call",
    "blocked_basis",
    "blocked_minutes",
    "builds_today",
    "call_build_modes",
    "capacity_left",
    "day_load",
    "decisions",
    "has_tables",
    "incremental",
    "load_model",
    "observations",
    "pauses",
    "plan_day",
    "plan_days",
    "plan_providers",
    "plan_receipts",
    "pressed_waits_on",
    "render_minutes_left",
    "render_minutes_today",
    "report_block",
    "started_today",
    "waits",
]
