"""The one read behind ``learnloop why``, the sidecar's ``why.get``, ``router trace`` and ``trace-evidence`` (ADR-017).

:func:`answer` takes a target (``latest``, a trace id, a record id, ``<subject_kind>:<id>``, ``item:<id>`` or a
practice item id) and returns, for each decision it names: what was chosen; the alternatives, each with its score
or probability and the rule it lost by; the inputs as of then; who decided, with versions and seed; what happened
next (the records naming it as their parent, the router outcome); and what was discarded (calls of the trace that
finished after the decision, or whose decision was never made). Decisions older than their records answer through
:mod:`learnloop.why.reconstructed`, labelled ``reconstructed``.

It is a pure read: the caller hands it a read-only repository, and nothing here writes, syncs or runs maintenance.
Payloads (prompts and outputs) never enter an answer; :func:`payloads` reads them from the receipts for the
desktop CLI's ``--payload`` only, and :func:`codes_only` is what the RPC returns.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop import provenance
from learnloop.why import reconstructed as R

VERSION = 1
#: The kind ``--first-build`` reads (``figures.records.KIND_PREBUILD``, named here so the reader needs no figures import).
FIGURE_PREBUILD = "figure_prebuild"
#: Kinds the reconstructed reader can answer, so ``--kind`` with another kind never falls back to it.
RECONSTRUCTED_KINDS = frozenset({"plan_block", "plan_interrupt", "today_offer", "staged_p2", "learner_pick",
                                 "lesson_suggestion", "offer_withdrawn", "figure_author", FIGURE_PREBUILD})


# -- one decision's answer ---------------------------------------------------------------------------------------


#: The outcome fields an answer shows (``router_outcomes``' columns, as the derivation names them).
OUTCOME_FIELDS = ("action_status", "action_attempt_id", "r_next_status", "r_next_value", "r_cold_status",
                  "r_cold_value")


def outcome_reader(repository: Any, loaded: Any) -> R.OutcomeReader:
    """``outcome(connection, decision_id)``: a router decision's outcome as of now, derived from the ledgers at read
    time once per answer (``why.outcomes_now``, the derivation ``learnloop router decisions`` shows). Not the
    ``router_outcomes`` table: that is a rebuild cache, stale for any decision made or answered since the last
    rebuild. Without the vault (its servable items and outcome version) nothing derives it, so the outcome is None,
    as it is when the derivation cannot run on an older schema."""

    derived: dict[str, Any] = {}

    def outcome(connection: Any, decision_id: str) -> dict[str, Any] | None:
        if loaded is None:
            return None
        if "rows" not in derived:
            from learnloop.why.outcomes_now import outcomes_now

            try:
                derived["rows"] = outcomes_now(connection, loaded, repository.sqlite_path)
            except (sqlite3.Error, ValueError, KeyError, TypeError):
                derived["rows"] = {}
        row = derived["rows"].get(str(decision_id))
        if row is None:
            return None
        return {**{key: R.code(row.get(key)) for key in OUTCOME_FIELDS}, "basis": "derived_at_read"}

    return outcome


def objective_trace_pointer(connection: Any, decision_id: str) -> dict[str, Any] | None:
    """The router objective trace of a router decision, as ids and versions (``learnloop router trace`` shows it)."""

    row = R.select_one(connection, "SELECT decision_id, trace_version, objective_version, content_hash FROM "
                             "router_objective_traces WHERE decision_id = ?", (decision_id,))
    return {key: R.code(value) for key, value in row.items()} if row else None


#: Stored fact names an answer shows under a clearer one. ``waited_ms`` is the time from the prefetch's start to the
#: decision, not how long any model was waited for (the configured wait is ``timeout_s``).
INPUT_NAMES = {"waited_ms": "prefetch_to_decision_ms"}
#: Why an alternative of a routing decision has the probability it shows (``p_basis``).
_OUTSIDE = frozenset({"outside_support", "infeasible"})


def _inputs(facts: Mapping[str, Any]) -> dict[str, Any]:
    return {INPUT_NAMES.get(name, name): value for name, value in facts.items()}


def _alternatives(connection: Any, record: provenance.DecisionRecord) -> list[dict[str, Any]]:
    """A decision's alternatives; a routing decision's each with its probability under the mix and where that comes
    from (``p_basis``): the record's own, the decision row's mix (stored or recomputed from its components), zero for
    an option outside the mix's support, or why there is none (a fallback drew from no mix; an older row kept none)."""

    alternatives = [dict(item) for item in record.alternatives]
    if record.kind != "plan_block":
        return alternatives
    mixture: dict[str, Any] | None = None
    for item in alternatives:
        if "p" in item:
            item["p_basis"] = "record"
        elif item.get("lost_by") in _OUTSIDE:
            item["p"], item["p_basis"] = 0.0, "outside_support"
        elif record.status == "fallback":
            item["p"], item["p_basis"] = None, "fallback_drew_no_mix"
        else:
            if mixture is None:
                row = R.select_one(connection, "SELECT detail_json FROM router_decisions WHERE id = ?",
                                   (record.detail_id,)) if record.detail_table == "router_decisions" else None
                try:
                    detail = json.loads(row["detail_json"] or "{}") if row else {}
                except ValueError:
                    detail = {}
                detail = detail if isinstance(detail, Mapping) else {}
                mixture = detail.get("mixture") if isinstance(detail.get("mixture"), Mapping) else {}
            pi, basis = R.mix_probabilities(mixture) if mixture else (None, "not_stored")
            item["p"] = (pi or {}).get(str(item.get("ref"))) if pi else None
            item["p_basis"] = basis if item["p"] is not None else "not_stored"
    return alternatives


def _decision(connection: Any, record: provenance.DecisionRecord, children: list[provenance.DecisionRecord],
              outcome_now: R.OutcomeReader) -> dict[str, Any]:
    router = record.detail_table == "router_decisions" and record.detail_id
    return {
        "record_id": record.id,
        "label": "native",
        "kind": record.kind,
        "status": record.status,
        "subject": f"{record.subject_kind}:{record.subject_id}" if record.subject_kind else None,
        "created_at": record.created_at,
        "trace_id": record.trace_id,
        "chosen": record.chosen_ref,
        "rule": record.rule,
        "alternatives": _alternatives(connection, record),
        "inputs": _inputs(record.facts),
        "decided_by": record.decided_by,
        "versions": dict(record.versions),
        "seed": record.versions.get("seed"),
        "error": {"type": record.error_type, "where": record.error_where} if record.error_type else None,
        "parent_id": record.parent_id,
        "detail": {"table": record.detail_table, "id": record.detail_id} if record.detail_table else None,
        "next": [{"record_id": child.id, "kind": child.kind, "status": child.status, "rule": child.rule,
                  "chosen": child.chosen_ref, "trace_id": child.trace_id, "created_at": child.created_at}
                 for child in children],
        "outcome": outcome_now(connection, str(record.detail_id)) if router else None,
        "objective_trace": objective_trace_pointer(connection, str(record.detail_id)) if router else None,
    }


# -- why --first-build ---------------------------------------------------------------------------------------------


#: Facts naming the candidate rather than what was measured about it: never "what changed".
_CANDIDATE_FACTS = frozenset({"request_key", "trigger_ref", "draw_index", "source", "verdict", "request_id",
                              "anchor", "decision_id"})


def _native_first_build(connection: Any) -> dict[str, Any] | None:
    """The last ``excluded`` pre-build before the first ``chosen`` one, and the facts that differ between them."""

    records = provenance.read_kind(connection, FIGURE_PREBUILD)
    first = next((index for index, record in enumerate(records) if record.status == "chosen"), None)
    if first is None:
        return None
    skips = [record for record in records[:first] if record.facts.get("verdict") == "skip"]
    last, built = (skips[-1] if skips else None), records[first]
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in dict.fromkeys(str(record.facts.get("trigger_kind")) for record in records):
        mine = [record for record in records if str(record.facts.get("trigger_kind")) == kind]
        index = next((i for i, record in enumerate(mine) if record.facts.get("verdict") != "skip"), len(mine))
        by_kind[kind] = {"skips_before_first_non_skip": sum(1 for record in mine[:index]
                                                            if record.facts.get("verdict") == "skip"),
                         "first_non_skip": mine[index].id if index < len(mine) else None}
    changed = {}
    if last is not None:
        for name in sorted(set(last.facts) | set(built.facts)):
            if name not in _CANDIDATE_FACTS and last.facts.get(name) != built.facts.get(name):
                changed[name] = [last.facts.get(name), built.facts.get(name)]
        for name in sorted(set(last.versions) | set(built.versions)):
            if last.versions.get(name) != built.versions.get(name):
                changed[f"versions.{name}"] = [last.versions.get(name), built.versions.get(name)]
    measured = R.first_measurement(connection)
    between = None
    if measured is not None and last is not None:
        at = R.moment(measured["at"])
        between = bool(at is not None and R.moment(last.created_at) < at <= R.moment(built.created_at))
    return {
        "label": "native",
        "kind": "figure_prebuild_first_build",
        "decisions_n": len(records),
        "skips_before_first_build": len(skips),
        "last_skip": {"record_id": last.id, "rule": last.rule, "created_at": last.created_at} if last else None,
        "first_build": {"record_id": built.id, "rule": built.rule, "created_at": built.created_at},
        "by_trigger_kind": by_kind,
        "by_trigger_kind_window": R.BY_KIND_WINDOW,
        "first_measurement": measured,
        "measurement_between": between,
        "changed": changed,
        "inferred": ["first_measurement", "measurement_between"],
        "_records": [record for record in (last, built) if record is not None],
    }


# -- the answer ----------------------------------------------------------------------------------------------------


def _records_answer(repository: Any, target: str, kind: str | None, *, first_build: bool,
                    timeout_now: float | None, outcome_now: R.OutcomeReader) -> dict[str, Any]:
    from learnloop.db.stores.provenance import discarded_calls, trace_model_calls, unclaimed_calls

    with repository.connection() as connection:
        built = None
        if first_build:
            built = _native_first_build(connection)
            records = list(built.pop("_records")) if built else []
            if built is None:
                built = R.first_build(connection)
        else:
            records = provenance.read(connection, target, kind=kind)
        traces = sorted({record.trace_id for record in records if record.trace_id})
        subject = target.partition(":")[0] in provenance.SUBJECT_KINDS and bool(target.partition(":")[2])
        if not records and kind is None and target != "latest" and not subject and not first_build \
                and trace_model_calls(connection, [target]):
            traces = [target]  # a trace whose models answered and nothing was decided (a key changed, an eviction)
        # A decision prefetched by an earlier request asked its models under that request's trace.
        prefetch = sorted({str(record.facts["prefetch_trace"]) for record in records
                           if record.facts.get("prefetch_trace")} - set(traces))
        calls = trace_model_calls(connection, [*traces, *prefetch])
        unclaimed = unclaimed_calls(connection, records, calls)
        discarded = discarded_calls(records, calls)
        children = provenance.read_children(connection, [record.id for record in records if record.id])
        decisions = [_decision(connection, record, [child for child in children if child.parent_id == record.id],
                               outcome_now)
                     for record in records]
        rebuilt: list[dict[str, Any]] = []
        if not records and not first_build and (kind is None or kind in RECONSTRUCTED_KINDS):
            rebuilt = R.resolve(connection, target, timeout_now=timeout_now, outcome_now=outcome_now)
            if kind is not None:
                rebuilt = [item for item in rebuilt if item["kind"] == kind]
            for item in rebuilt:
                row = item.get("row") or {}
                if row.get("table") == "router_decisions":
                    item["objective_trace"] = objective_trace_pointer(connection, str(row["id"]))
                # One place for what was discarded: the answer's own list, each entry naming its decision.
                discarded += [{**entry, "decision_id": row.get("id")} for entry in item.pop("discarded", None) or ()]
        evidence = attempt_evidence(connection, target.partition(":")[2]) if target.startswith("attempt:") else None
    if first_build:
        source = "reconstructed" if built is not None and built.get("label") == R.LABEL else "decision_records"
    else:
        source = "reconstructed" if rebuilt and not records else "decision_records"
    answer: dict[str, Any] = {
        "version": VERSION,
        "source": source,
        "target": target,
        "traces": traces,
        "prefetch_traces": prefetch,
        "records": [record.as_dict() for record in records],
        "model_calls": calls,
        "discarded": discarded,
        "unclaimed": unclaimed,
        "decisions": decisions,
        "reconstructed": rebuilt,
    }
    if first_build:
        answer["first_build"] = built
    if evidence is not None:
        answer["evidence"] = evidence
    return answer


def found_anything(answer: Mapping[str, Any]) -> bool:
    return bool(answer.get("records") or answer.get("model_calls") or answer.get("reconstructed")
                or answer.get("first_build"))


def answer(repository: Any, target: str | None = None, *, kind: str | None = None, first_build: bool = False,
           loaded: Any = None) -> dict[str, Any] | None:
    """Why the decisions ``target`` names went the way they did; None when nothing answers (``not_found``).

    ``loaded`` (the vault) is needed for a practice item's scheduler explanation and the router's wait as set now;
    without it only records and old rows answer. ``first_build`` reads the pre-builds (``kind`` defaults to
    ``figure_prebuild``): the last skip, the first build, and the measurement that changed between them.
    """

    target = target or "latest"
    if first_build:
        kind = kind or FIGURE_PREBUILD
    timeout_now = None
    if loaded is not None:
        router = getattr(getattr(loaded, "config", None), "router", None)
        timeout_now = getattr(router, "timeout_seconds", None)
    outcome_now = outcome_reader(repository, loaded)
    item_target = target.removeprefix("item:")
    if loaded is not None and not first_build and item_target in loaded.practice_items:
        explanation = scheduler_explanation(loaded, repository, item_target)
        if target.startswith("item:"):
            explanation = item_exclusions(loaded, repository, item_target, explanation)
            records = _records_answer(repository, target, kind, first_build=False, timeout_now=timeout_now,
                                      outcome_now=outcome_now)
            explanation["records"] = records["records"]
            explanation["decisions"] = records["decisions"]
        return explanation
    result = _records_answer(repository, target, kind, first_build=first_build, timeout_now=timeout_now,
                             outcome_now=outcome_now)
    subject = target.partition(":")[0] in provenance.SUBJECT_KINDS and bool(target.partition(":")[2])
    if not found_anything(result) and kind is None and target != "latest" and not subject and loaded is not None:
        # Not a record, a trace or an old row: an item no longer in the vault's files keeps its last explanation.
        return scheduler_explanation(loaded, repository, target)
    return result


# -- a practice item: today's scheduler explanation and its exclusions --------------------------------------------


#: Stored JSON a scheduler explanation reads; a malformed value is named, not raised (``why item:<id>``).
_JSON_COLUMNS = (("followup_tasks", "context_json"),)


def _bad_rows(repository: Any) -> list[dict[str, Any]]:
    found = []
    with repository.connection() as connection:
        for table, column in _JSON_COLUMNS:
            for row in R.select_rows(connection, f"SELECT id FROM {table} WHERE {column} IS NOT NULL AND "
                                           f"NOT json_valid({column}) ORDER BY id LIMIT 20"):
                found.append({"table": table, "id": R.code(row["id"]), "column": column})
    return found


def scheduler_explanation(loaded: Any, repository: Any, practice_item_id: str) -> dict[str, Any] | None:
    """Today's scheduler explanation of one item, computed without persisting it; else its latest stored one.

    A stored row it cannot parse degrades the answer instead of failing it: ``source = "unavailable"``, the
    exception's class and where it was raised, and the rows holding malformed JSON (never their content)."""

    from learnloop.scheduling.scheduler import explain_practice_item

    try:
        item = explain_practice_item(loaded, repository, practice_item_id)
    except (ValueError, TypeError) as exc:  # a malformed stored value (JSONDecodeError is a ValueError)
        return {"version": VERSION, "source": "unavailable", "practice_item_id": practice_item_id,
                "explanation_error": {"type": type(exc).__name__, "where": provenance.where(exc),
                                      "bad_rows": _bad_rows(repository)}}
    if item is None:
        latest = repository.latest_scheduler_explanation(practice_item_id)
        if latest is None:
            return None
        return {"version": VERSION, "source": "latest", "explanation": latest}
    return {
        "version": VERSION,
        "source": "current",
        "practice_item_id": item.practice_item_id,
        "priority": item.priority,
        "components": item.components,
        "readiness_factor": item.readiness_factor,
        "reasons": item.plain_english,
    }


def item_exclusions(loaded: Any, repository: Any, practice_item_id: str,
                    explanation: dict[str, Any] | None) -> dict[str, Any]:
    """``item:<id>``: the newest slate records naming the item, and, off today's slate, the rule keeping it off.

    A slate record names only a few ids per exclusion rule, so an item it
    counts without naming is answered by a build now (persisting nothing).
    """

    from learnloop.scheduling.scheduler import exclusion_now
    from learnloop.scheduling.slate_record import KIND, item_outcome

    result = dict(explanation) if explanation is not None else {
        "version": VERSION, "source": "none", "practice_item_id": practice_item_id,
    }
    with repository.connection() as connection:
        records = provenance.read_naming(connection, practice_item_id, kind=KIND)
    result["slates"] = [
        {"record_id": record.id, "trace_id": record.trace_id, "created_at": record.created_at,
         "slate_id": record.detail_id, "outcome": item_outcome(record, practice_item_id)}
        for record in records
    ]
    if result["source"] != "current":
        try:
            result["excluded_now"] = exclusion_now(loaded, repository, practice_item_id)
        except (ValueError, TypeError) as exc:  # the same malformed row the explanation named
            result["excluded_now"] = None
            result.setdefault("explanation_error", {"type": type(exc).__name__, "where": provenance.where(exc),
                                                    "bad_rows": _bad_rows(repository)})
    return result


# -- an attempt's evidence; the reports this reader also serves ---------------------------------------------------


def attempt_evidence(connection: Any, attempt_id: str) -> list[dict[str, Any]]:
    """The facets the grader saw an attempt exercise (A6), as ids and codes; the grader's words stay in the table."""

    if not attempt_id:
        return []
    return [{key: R.code(value) for key, value in row.items()} for row in R.select_rows(
        connection, "SELECT facet_id, observation_scope, source, criterion_id, grading_prompt_version, created_at "
                    "FROM trace_exercised_facets WHERE attempt_id = ? ORDER BY facet_id, source", (attempt_id,))]


def evidence_report(repository: Any) -> dict[str, Any]:
    """``learnloop trace-evidence``: A6's concentration and A1 guard 1's unexercised supporting mass."""

    from learnloop.attempts.trace_evidence import trace_evidence_report

    return trace_evidence_report(repository)


def objective_trace(connection: Any, decision: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """``learnloop router trace``: one decision's router objective trace and, for a drawn lesson offer, its binding.

    Raises ``ValueError`` on a database older than the trace table (migration 246)."""

    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective.offer_report import binding

    if not store.table_present(connection, store.TRACES):
        raise ValueError("this database predates the router objective's trace (migration 246)")
    row = store.trace(connection, decision)
    # Teacher TE3b: a drawn lesson offer's binding (decision -> response -> lesson -> receipt -> delayed checks), a
    # read over existing ids; None for every other decision.
    return row, (binding(connection, str(row["decision_id"])) if row is not None else None)


# -- payloads (desktop CLI only) and the RPC's codes-only view -----------------------------------------------------


def call_ids(answer: Mapping[str, Any]) -> list[str]:
    """Every model call an answer names: its traces' calls, the discarded and unclaimed ones, the reconstructed."""

    ids: list[str] = []
    for call in answer.get("model_calls") or ():
        ids.append(call.get("id"))
    for entry in [*(answer.get("discarded") or ()), *(answer.get("unclaimed") or ())]:
        ids.append(entry.get("call_id"))
    for item in answer.get("reconstructed") or ():
        ids.extend(call.get("call_id") for call in item.get("calls") or ())
    return [str(item) for item in dict.fromkeys(ids) if item]


def payloads(repository: Any, ids: Iterable[str]) -> list[dict[str, Any]]:
    """The prompt and output each call's receipt holds, under the receipts' own retention. ``learnloop why --payload``
    on the desktop CLI is the only caller: ``why.get`` never returns a payload."""

    wanted = sorted({str(item) for item in ids if item})
    if not wanted:
        return []
    with repository.connection() as connection:
        try:
            rows = connection.execute(
                f"SELECT id, purpose, status, input_text, output_text FROM model_call_receipts "
                f"WHERE id IN ({', '.join('?' for _ in wanted)}) ORDER BY started_at, id", wanted).fetchall()
        except sqlite3.OperationalError:
            return []
    return [{"call_id": row[0], "purpose": row[1], "status": row[2], "input_text": row[3], "output_text": row[4]}
            for row in rows]


#: Fields whose strings are free text however they are spelled: one word of model or learner text ("photosynthesis")
#: passes the code check, so under these names every string, and every key, is withheld. ``unsupported_kind`` is
#: the figure author's own words; ``reasons`` and ``explanation`` the scheduler's plain English; the rest name the
#: payloads and learner text no answer should hold.
TEXT_FIELDS = frozenset({
    "unsupported_kind", "unsupported_reason", "why_not_spec", "reasons", "plain_english", "explanation",
    "rationale", "input_text", "output_text", "prompt", "answer_md", "work_md", "hint_md", "explanation_text",
    "learner_answer", "title", "message",
})


def codes_only(value: Any, path: str = "") -> tuple[Any, list[str]]:
    """``value`` with every string that is not an id, a number or a code (:func:`provenance.is_code`) removed, every
    string and key under a :data:`TEXT_FIELDS` name removed whatever its spelling, and the paths removed. The RPC
    returns this, so a field that holds prose (an item's plain-English reasons, a latest stored explanation, a
    figure author's words) never leaves the desktop through it."""

    withheld: list[str] = []

    def visit(item: Any, where: str, text: bool) -> Any:
        if item is None or isinstance(item, (bool, int, float)):
            return item
        if isinstance(item, str):
            if not text and provenance.is_code(item):
                return item
            withheld.append(where)
            return None
        if isinstance(item, Mapping):
            out = {}
            for key, inner in item.items():
                if text or not provenance.is_code(str(key)):
                    withheld.append(f"{where}.<key>")
                    continue
                out[str(key)] = visit(inner, f"{where}.{key}" if where else str(key), str(key) in TEXT_FIELDS)
            return out
        if isinstance(item, (list, tuple)):
            return [visit(inner, f"{where}[{index}]", text) for index, inner in enumerate(item)]
        withheld.append(where)
        return None

    return visit(value, path, False), withheld
