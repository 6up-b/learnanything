"""The figures' decision records (ADR-017, refactor B4): why a figure was built ahead of need or not, and why an author's attempt was kept or not.

Four kinds, each a :class:`learnloop.provenance.DecisionRecord` of ids, numbers and codes
(never a goal, a passage, a prompt or the author's text):

* ``figure_prebuild``: one per candidate the prefetch model decided (``figures.prefetch``):
  its verdict as the status, the model's rule (:data:`~.prefetch_model.RULE_NO_MEASURED_LATENCY`
  and its two siblings), EU, propensity, the measured-wait summary the draw read, and the pass's
  RNG seed. ``detail`` is its ``figure_prefetch_decisions`` row.
* ``figure_prefetch_filter``: one per filter pass that excluded anything: the count by rule and
  up to :data:`MAX_KEYS_PER_RULE` request keys per rule, protection exclusions included.
* ``figure_prebuild_stop``: a build the queue stopped at or passed over (the in-memory notes'
  reasons, as codes).
* ``figure_author``: one per author attempt, with its typed problem codes, so attempt 1's problems
  survive attempt 2. ``detail`` is the stored ``interactive_figures`` row when there is one.

The builders here are pure; the shell writes their records with :func:`write_records`, which
never raises, so a record can't change the decision it describes.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop import provenance
from learnloop.db.stores.provenance import write_decision

_LOG = logging.getLogger(__name__)

KIND_PREBUILD = "figure_prebuild"
KIND_FILTER = "figure_prefetch_filter"
KIND_BUILD_STOP = "figure_prebuild_stop"
KIND_AUTHOR = "figure_author"

#: Request keys kept per exclusion rule (the rest are counted).
MAX_KEYS_PER_RULE = 10

# -- the filter's rules, in the order filter_candidates applies them ------------------------------------
FILTER_PROTECTION_UNAVAILABLE = "protection_unavailable"
FILTER_DUPLICATE = "duplicate_in_pass"
FILTER_OPEN_HORIZON = "decided_horizon_open"
FILTER_DECIDED = "decided_for_trigger"
FILTER_NO_SPANS = "no_spans"
FILTER_SHOW_ME_OFF = "show_me_off"
FILTER_WITHHELD = "withheld"
FILTER_GROUNDING_WITHHELD = "grounding_withheld"
FILTER_ITEM_PROTECTED = "item_protected"
FILTER_ALREADY_BUILT = "already_built"

# -- the build queue's stops ---------------------------------------------------------------------------
STOP_FOREGROUND = "foreground_busy"
STOP_RICH_IN_FLIGHT = "rich_in_flight"
STOP_OFF_MAINS = "off_mains"
STOP_AUTHOR_NOT_PLAN = "author_not_plan"
STOP_ITEM_PROTECTED = "item_protected"
STOP_BUILT_ALREADY = "built_already"
STOP_RENDER_MINUTES = "render_minutes_used"
STOP_DAILY_BUILDS = "daily_builds_used"
STOP_BUILD_REFUSED = "build_refused"
STOP_BUILD_FAILED = "build_failed"
STOP_RICH_JOB_RUNNING = "rich_job_running"

# -- the author's problem codes ------------------------------------------------------------------------
#: The model call raised (its exception class is the record's ``error_type``).
MODEL_FAILED = "model_failed"
#: A V3 status outside the media offered (or a V2 status outside spec/sketch/unsupported).
STATUS_INVALID = "status_invalid"
#: A V3 answer with no ``why_this_tier``.
TIER_REASON_MISSING = "tier_reason_missing"
#: Free text that reads like a code-owned check label (spec §9b.4).
LABEL_TEXT = "label_text"
#: The label text was still there on the last attempt and was stripped (the figure kept).
LABEL_TEXT_STRIPPED = "label_text_stripped"
#: A spec or sketch refused by its parser for a prediction's own problem.
PREDICTION_INVALID = "prediction_invalid"
#: Bad predictions dropped and the figure kept (``spec.parse_salvaging_predictions``).
PREDICTION_DROPPED = "prediction_dropped"
#: A spec refused by its parser (schema, caps, grammar).
SPEC_INVALID = "spec_invalid"
#: A sketch program refused by its parser.
SKETCH_INVALID = "sketch_invalid"
#: A rich tier's brief refused by its parser.
BRIEF_INVALID = "brief_invalid"
#: The numeric verification (steps 1-2), the sketch's run, or the sketch engine itself failed.
VERIFICATION_FAILED = "verification_failed"
#: RW5c's step 3 proved a stated claim different from the source.
SOURCE_DIFFERS = "source_differs"
#: A rich answer's optional quick figure was dropped (the rich half carries on).
QUICK_DROPPED = "quick_dropped"
#: The attempt's answer is the figure (``unsupported`` when the author said it can't be drawn).
ACCEPTED = "accepted"
UNSUPPORTED = "unsupported"
#: The build raised before or after its attempts, with no refusal code of its own.
BUILD_ERROR = "build_error"
#: An attempt the build never reached a verdict on (the build stopped inside it).
INTERRUPTED = "interrupted"

_KEPT = frozenset({ACCEPTED, UNSUPPORTED, PREDICTION_DROPPED})
#: The author statuses a record names; any other status the model wrote is recorded as ``other``.
_AUTHOR_STATUSES = frozenset({"spec", "sketch", "unsupported", "js_animation", "manim"})
_PREDICTION_PROBLEM = re.compile(r"^prediction \d+:")


def code(value: Any) -> str | None:
    """``value`` when it is an id or a code constant (``provenance.check_no_prose``), else a short
    hash of it, so a ref that happens to hold text never carries the text and never drops the record."""

    if value is None:
        return None
    text = str(value)
    if not provenance.check_no_prose(provenance.DecisionRecord(kind=text, status="chosen")):
        return text
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def number(value: Any, digits: int | None = None) -> float | None:
    """A finite float (rounded to ``digits`` when given), or None."""

    if value is None or isinstance(value, bool):
        return None
    try:
        found = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(found):
        return None
    return round(found, digits) if digits is not None else found


def write_records(repository: Any, records: Iterable[provenance.DecisionRecord]) -> list[str | None]:
    """Write each record with its own short transaction (``write_decision``); never raises."""

    return [write_decision(repository, record) for record in records]


def in_one_trace(records: Sequence[provenance.DecisionRecord]) -> list[provenance.DecisionRecord]:
    """The records under the current trace, or one trace born for all of them (outside every
    entry point each write would otherwise birth its own)."""

    trace = provenance.current_trace() or provenance.new_trace_id()
    return [record if record.trace_id else replace(record, trace_id=trace) for record in records]


# ---------------------------------------------------------------------------
# Prefetch
# ---------------------------------------------------------------------------

def prebuild_record(row: Mapping[str, Any], decision: Any, model: Any, *, draw_index: int, seed: str | None,
                    builds_left: int, render_left: float, on_mains: bool, plan_waiting: bool,
                    expected_requests: float) -> provenance.DecisionRecord:
    """The ``figure_prebuild`` record of one decided candidate (``row`` is its ledger row)."""

    verdict = str(row["decision"])
    status = {"build": "chosen", "skip": "excluded"}.get(verdict, "deferred")
    kind = str(row["trigger_kind"])
    waits = model.waits
    facts = {
        "verdict": verdict, "draw_index": int(draw_index), "trigger_kind": kind,
        "trigger_ref": code(row.get("trigger_ref")), "request_key": code(row.get("request_key")),
        "source_key": code(row.get("source_key")), "p_content": number(row.get("p_open_content")),
        "p_open": number(decision.p_open), "eu": number(decision.sampled_eu),
        "propensity": number(decision.propensity), "benefit_min": number(decision.w_minutes),
        "cost_min": number(decision.cost_minutes), "wait_min": number(waits.expected(kind)),
        "wait_basis": waits.basis(kind),
        "waits_n": _measurements(waits),
        "waits_n_by_tier": {str(tier): int(value) for tier, value in sorted(waits.counts.items())},
        "wait_min_by_tier": {str(tier): number(value, 4) for tier, value in sorted(waits.minutes.items())},
        "blocked_min": number(model.blocked_minutes), "load_today": number(model.load_today),
        "expected_requests": number(expected_requests), "observations": int(model.opening.observations),
        "pause_days": int(model.pause.days), "builds_left": int(builds_left), "render_left_min": number(render_left),
        "on_mains": bool(on_mains), "plan_waiting": bool(plan_waiting),
    }
    return provenance.DecisionRecord(
        kind=KIND_PREBUILD, status=status, subject_kind="decision", subject_id=str(row["id"]),
        chosen_ref=code(row.get("request_key")) if verdict == "build" else None,
        decided_by=str(row.get("model_version") or ""), rule=decision.rule or None, facts=facts,
        versions={"model_version": row.get("model_version"), "posterior_digest": row.get("posterior_digest"),
                  "seed": seed if seed is not None else "injected", "posterior_draws": _posterior_draws()},
        detail_table="figure_prefetch_decisions", detail_id=str(row["id"]),
    )


def _measurements(waits: Any) -> int:
    """The measured latencies behind W: the quick tiers share one sample (the author call's
    duration counts for grammar and sketch alike), each rich tier's are its own requests."""

    from learnloop.figures.prefetch_model import QUICK_TIERS

    quick = max((int(waits.counts.get(tier, 0)) for tier in QUICK_TIERS), default=0)
    return quick + sum(int(value) for tier, value in waits.counts.items() if tier not in QUICK_TIERS)


def _posterior_draws() -> int:
    from learnloop.figures.prefetch_model import POSTERIOR_DRAWS

    return int(POSTERIOR_DRAWS)


@dataclass
class FilterLog:
    """One filter pass's exclusions by rule (request keys), and what it kept."""

    found: int = 0
    kept: int = 0
    excluded: list[tuple[str, str, str]] = field(default_factory=list)
    trigger_kinds: set[str] = field(default_factory=set)

    def exclude(self, rule: str, candidate: Any) -> None:
        try:
            key = str(candidate.request_key)
        except Exception:  # noqa: BLE001 - the exclusion is still counted; only its key is lost
            key = "unknown"
        self.excluded.append((rule, key, str(getattr(candidate, "trigger_kind", ""))))

    def record(self) -> provenance.DecisionRecord | None:
        """The ``figure_prefetch_filter`` record, or None when nothing was excluded."""

        if not self.excluded:
            return None
        counts: dict[str, int] = {}
        alternatives: list[dict[str, Any]] = []
        for rule, key, _kind in self.excluded:
            counts[rule] = counts.get(rule, 0) + 1
            if counts[rule] <= MAX_KEYS_PER_RULE:
                alternatives.append({"ref": code(key), "lost_by": rule})
        rules = sorted(counts)
        return provenance.DecisionRecord(
            kind=KIND_FILTER, status="excluded", decided_by="prefetch_filters",
            rule=rules[0] if len(rules) == 1 else "several_rules", alternatives=alternatives,
            facts={"found": int(self.found), "kept": int(self.kept), "excluded": len(self.excluded),
                   "excluded_by_rule": dict(sorted(counts.items())),
                   "trigger_kinds": sorted(code(kind) for kind in self.trigger_kinds)},
        )


def build_stop_record(rule: str, status: str, decision_id: str, *, waiting: Sequence[str] = (),
                      error: BaseException | None = None, refusal: str | None = None) -> provenance.DecisionRecord:
    """A ``figure_prebuild_stop`` record: the build of ``decision_id`` stopped (``deferred``: it and
    the queue after it wait for a later pass), passed over (``excluded``), refused or failed."""

    facts: dict[str, Any] = {"waiting": len(waiting), "waiting_ids": [code(item) for item in waiting[:MAX_KEYS_PER_RULE]]}
    if refusal is not None:
        facts["refusal"] = code(refusal)
    return provenance.DecisionRecord(
        kind=KIND_BUILD_STOP, status=status, subject_kind="decision", subject_id=code(decision_id),
        decided_by="prefetch_build_guards", rule=rule, facts=facts,
        detail_table="figure_prefetch_decisions", detail_id=code(decision_id),
        error_type=type(error).__name__ if error is not None else None,
        error_where=provenance.where(error) if error is not None else None,
    )


# ---------------------------------------------------------------------------
# The author's attempts
# ---------------------------------------------------------------------------

def spec_problem(problems: Sequence[str]) -> str:
    """A parser's problems as a code: a prediction's own problem, or the spec's."""

    return PREDICTION_INVALID if any(_PREDICTION_PROBLEM.match(str(item)) for item in problems) else SPEC_INVALID


def sketch_problem(problems: Sequence[str]) -> str:
    return PREDICTION_INVALID if any(_PREDICTION_PROBLEM.match(str(item)) for item in problems) else SKETCH_INVALID


@dataclass
class _Attempt:
    number: int
    rule: str | None = None
    status: str | None = None
    extra: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    error: BaseException | None = None


@dataclass
class AuthorAttempts:
    """What each author attempt came to, noted as the loop runs (list appends only: nothing here can
    change the loop's control flow), and written as ``figure_author`` records when the build ends."""

    attempts: list[_Attempt] = field(default_factory=list)
    prompt_version: str | None = None

    def start(self, number: int) -> None:
        self.attempts.append(_Attempt(number))

    @property
    def current(self) -> _Attempt | None:
        return self.attempts[-1] if self.attempts else None

    def end(self, rule: str, *, status: str | None = None, error: BaseException | None = None,
            problems: int | None = None) -> None:
        """The current attempt's verdict: ``rule`` its code (a retry follows, or it was the last)."""

        attempt = self.current
        if attempt is None:
            return
        attempt.rule, attempt.status, attempt.error = rule, status, error
        if problems is not None:
            attempt.facts["problems_n"] = int(problems)

    def extra(self, problem: str) -> None:
        if self.current is not None and problem not in self.current.extra:
            self.current.extra.append(problem)

    def fact(self, **facts: Any) -> None:
        if self.current is not None:
            self.current.facts.update(facts)

    def records(self, *, request: Any, request_id: str | None, model: Any, outcome: Any = None,
                error: BaseException | None = None) -> list[provenance.DecisionRecord]:
        """One record per attempt (one for the refusal when the build stopped before any)."""

        figure_id, job_id, result = _outcome(outcome, error)
        for attempt in self.attempts:
            if attempt.facts.get("predictions_dropped") and PREDICTION_DROPPED not in attempt.extra:
                attempt.extra.append(PREDICTION_DROPPED)
        attempts = list(self.attempts) or [_Attempt(0)]
        if not self.attempts:
            refusal = getattr(error, "code", None)
            attempts[0].rule = code(refusal) if refusal else BUILD_ERROR
            attempts[0].status = "refused" if refusal else "failed"
            attempts[0].error = None if refusal else error
        last = attempts[-1]
        if last.rule is None:
            if error is not None:
                last.rule, last.status, last.error = INTERRUPTED, "failed", error
            elif PREDICTION_DROPPED in last.extra:
                last.rule = PREDICTION_DROPPED
            else:
                last.rule = ACCEPTED
        common = {"request_id": code(request_id), "origin": code(getattr(request, "origin", None)),
                  "attempts": len(self.attempts), "outcome": result,
                  "prefetch_decision_id": code(getattr(request, "prefetch_decision_id", None))}
        versions = {"prompt_version": code(self.prompt_version), "model": code(model)}
        records = []
        for index, attempt in enumerate(attempts):
            rule = attempt.rule or INTERRUPTED
            if attempt.status is not None:
                status = attempt.status
            elif rule in _KEPT:
                status = "chosen"
            else:
                status = "discarded" if index < len(attempts) - 1 else "failed"
            author_status = attempt.facts.get("author_status")
            problems = [rule, *(item for item in attempt.extra if item != rule)]
            facts = {**common, "attempt": attempt.number, "problems": problems,
                     **{name: value for name, value in attempt.facts.items() if name != "author_status"}}
            if author_status is not None:
                facts["author_status"] = author_status if author_status in _AUTHOR_STATUSES else "other"
            chosen = status == "chosen"
            records.append(provenance.DecisionRecord(
                kind=KIND_AUTHOR, status=status,
                subject_kind="figure" if figure_id else "job" if job_id else None, subject_id=figure_id or job_id,
                chosen_ref=(figure_id or job_id) if chosen else None, decided_by="figure_author",
                rule=rule, facts=facts, versions=versions,
                detail_table="interactive_figures" if figure_id else None, detail_id=figure_id,
                error_type=type(attempt.error).__name__ if attempt.error is not None else None,
                error_where=provenance.where(attempt.error) if attempt.error is not None else None,
            ))
        return in_one_trace(records)

    def write(self, repository: Any, **kwargs: Any) -> None:
        """:meth:`records`, written; never raises (a record never changes the build it describes)."""

        try:
            records = self.records(**kwargs)
        except Exception as exc:  # noqa: BLE001 - the build's result stands without its records
            _LOG.warning("figure_author records not built (trace %s): %s", provenance.current_trace(),
                         type(exc).__name__)
            return
        write_records(repository, records)


def _outcome(outcome: Any, error: BaseException | None) -> tuple[str | None, str | None, str]:
    """The stored (or reused) figure's id, a rich-only build's job id, and the build's result as a code."""

    if error is not None:
        refusal = getattr(error, "code", None)
        return None, None, code(refusal) if refusal else BUILD_ERROR
    view = getattr(outcome, "view", None) or {}
    figure_id = view.get("figure_id") or view.get("figureId") or view.get("id")
    rich = getattr(outcome, "rich", None)
    if rich and not figure_id:
        return None, code(rich.get("rich_job_id")) if isinstance(rich, Mapping) else None, "rich_pending"
    if getattr(outcome, "reused", False):
        return code(figure_id), None, "reused"
    verification = view.get("verification")
    return code(figure_id), None, code(verification) or "stored"


__all__ = [
    "ACCEPTED",
    "AuthorAttempts",
    "BRIEF_INVALID",
    "FilterLog",
    "KIND_AUTHOR",
    "KIND_BUILD_STOP",
    "KIND_FILTER",
    "KIND_PREBUILD",
    "LABEL_TEXT",
    "MAX_KEYS_PER_RULE",
    "MODEL_FAILED",
    "PREDICTION_DROPPED",
    "PREDICTION_INVALID",
    "SOURCE_DIFFERS",
    "SPEC_INVALID",
    "STATUS_INVALID",
    "VERIFICATION_FAILED",
    "build_stop_record",
    "code",
    "in_one_trace",
    "number",
    "prebuild_record",
    "write_records",
]
