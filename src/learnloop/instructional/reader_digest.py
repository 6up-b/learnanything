"""Reader workbench RW6b part 2: the session narrative (spec_reader_workbench_v1
§9.2, §9.5, §9.6; UX §4.8, W14).

After a reader session RW6b part 1 planned (its ``reader_session_digests``
row; with follow-ups not live, a summary-only row this module writes,
:func:`summarize_ended_sessions`, Codex review F2), one background call on route ``reader_digest`` writes **at most 120
words** about what the learner did, from the session's **typed summary
only** (the summary stored on the digest row: ids, kinds, statuses and
verdicts, never the learner's words) plus the titles of the topics and
sections it names. The model cites the summary's event ids; code checks
them (:func:`validate_narrative`): every cited id must be in the summary
(:func:`citable_ids`), at least one must be cited, and the text must keep to
the word bound. A narrative that fails is **dropped** and why is recorded
(``judgment_ledger``, task ``reader_digest_narrative``, verdict ``dropped``
with its reasons; a kept one is recorded ``kept``).

* **Once per session.** Before anything is asked, the session's durable
  claim is taken (``judgment_work_claims``, task :data:`CLAIM_TASK`; Codex
  review F3), so two processes never pay for one narrative; its liveness is
  re-checked before every request and, under the write lock, at
  publication (re-review F3), so a worker whose lease lapsed or was taken
  over neither sends nor publishes (its paid answer is checkpointed for the
  next holder). The narrative
  is written to the digest row's narrative columns (``narrative_md``, ``cited_event_ids_json``, ``model``,
  ``prompt_version``) by :func:`learnloop.db.stores.reader_digests.set_narrative`;
  ``prompt_version`` marks the session as narrated whether the narrative was
  kept or dropped, so a dropped one is never paid for again. Conditions that
  last only while they hold (the plan is unavailable, today's metered cap is
  spent, no price for a metered route) write nothing and are retried at the
  next Today build; :func:`narrative_view` shows them in W14's words.
* **Routed, capped, receipted.** :class:`NarrativeRoute` plans the route
  (``ai.routing.reader_digest``, unset: the active provider, the ChatGPT plan
  under T1) and sends through ``PaidCalls`` (receipts, the per-call caps). A
  metered call needs ``digest.price_per_million`` and is held to
  ``digest.max_daily_cost_usd``; subscription calls are ``estimated_only``.
  The work runs in the background (never on a request path), where no
  OpenRouter grant exists: a plan that is down means no narrative, and no
  offer is made.
* **Never evidence** (W1 tier 1, ``salience_only``). Nothing in scoring,
  scheduling, projection, grading, serving or replay reads the narrative, it
  is never a source of a filled mark, and it is shown collapsed, labelled
  "summary written by LearnLoop's model". An import-linter contract keeps
  everything that writes evidence from importing this module.
* **Exam material.** A session whose inquiries or formative records are
  anchored in passages the one exam predicate withholds is never sent; it is
  recorded as dropped (``exam_material``).

Switches: ``digest.enabled`` and ``digest.narrative_enabled`` (off: no route
call and no narrative anywhere, RW6b part 1 exactly). Without an injected
client, ``LEARNLOOP_DIGEST_MODELS=off`` (set by the test suite) reaches no
model.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
import threading
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendLimitExceeded, spend_envelopes
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import reader_digests as RDG
from learnloop.db.stores.judgments import append_judgment
from learnloop.practice_index.paid import PaidCalls, PaidRoute, plan_route, resolve_client
from learnloop.reader import recap as RC
from learnloop.reader import reader_sessions as RS

ROUTE_TASK = "reader_digest"
PURPOSE = "reader_digest"
OWNER_KIND = "reader_digest"
PROMPT_VERSION = "reader_digest.v1"
#: The ``judgment_ledger`` task of the narrative's verdict (kept or dropped, with why).
LEDGER_TASK = "reader_digest_narrative"
LEDGER_LEFT = "reader_session_digest"
ENVELOPE = "digest.max_daily_cost_usd"
MODELS_ENV = "LEARNLOOP_DIGEST_MODELS"
NARRATIVE_VERSION = "rw6b-narrative-v1"
#: Spec §9.2: "at most 120 words" (a structural bound of the design, not a parameter).
MAX_WORDS = 120
#: The label every surface shows with the narrative (spec §9.2, UX §4.8), and
#: its authority (W1 tier 1: salience only; never evidence, never a filled mark).
LABEL = RDG.NARRATIVE_LABEL
AUTHORITY = RDG.NARRATIVE_AUTHORITY
#: One narrative's paid-call bounds (the call and a retry of a malformed
#: answer): runaway-loop bounds, not money (money is the daily envelope).
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=2, max_calls=3, max_total_tokens=80_000)

_INSTRUCTIONS = (
    "Write a short summary, addressed to the learner as \"you\", of one reading session, from the typed "
    "summary below only. Say what they read, which questions they opened, resolved or left open, which "
    "problems they worked and with how much help, and what is worth a second look. At most 120 words, plain "
    "prose, no lists, no headings, no ids or brackets in the text. Never say they mastered, know or "
    "demonstrated anything, never grade them, and never say \"error\" or \"mistake\" about their work. Cite "
    "in cited_event_ids the ids (from citable_event_ids) of the summary entries your sentences describe; "
    "cite at least one, and nothing that is not in citable_event_ids."
)

#: The knowledge well's markers (UX §3.4): evidence's vocabulary, never a narrative's.
EVIDENCE_MARKERS = ("●", "◌", "○")

#: The W14 states :func:`narrative_view` reports (``off`` is no view at all).
STATES = ("pending", "landed", "failed", "unreachable", "capped")


class ReaderDigestNarrativeV1(WireModel):
    """The narrative and the summary ids it cites (strict)."""

    narrative: str
    cited_event_ids: list[str]


@dataclass
class NarrativeResult:
    """What one narration did. ``status``: narrated | dropped | disabled |
    no_digest | already | claimed (another process holds the session's
    claim) | not_ended | unavailable | capped | unpriced | models_off |
    unrouted | failed."""

    status: str
    digest_id: str
    reason: str | None = None
    reasons: list[str] = field(default_factory=list)
    model: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class NarrativeUnavailable(Exception):
    """Refused before any call (the reason lasts only while it holds)."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


# ---------------------------------------------------------------------------
# Switches
# ---------------------------------------------------------------------------

def _config(vault: Any) -> Any:
    return getattr(vault.config, "digest", None)


def digest_enabled(vault: Any) -> bool:
    """RW6b part 2 as a whole (``digest.enabled``): the narrative and the
    router card's reader section."""

    return bool(getattr(_config(vault), "enabled", True))


def narrative_enabled(vault: Any) -> bool:
    """``digest.enabled`` and ``digest.narrative_enabled``: off, no route call
    and no narrative anywhere."""

    return digest_enabled(vault) and bool(getattr(_config(vault), "narrative_enabled", True))


def models_off() -> bool:
    return os.environ.get(MODELS_ENV, "").strip().lower() == "off"


# ---------------------------------------------------------------------------
# The summary's citable ids and the narrative's checks (pure)
# ---------------------------------------------------------------------------

def _ids(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if value not in (None, "")]


def citable_ids(summary: Mapping[str, Any]) -> set[str]:
    """Every event id the typed summary carries (``ReaderSessionSummaryV1``):
    the inquiries' root exchanges and question events, every Ask exchange of
    the session, the workbench sessions and their attempts, the formative
    records' source events (and their inquiry roots), the gaps named and the
    questions they were named from, and the attempts behind each claim
    needing an independent check."""

    out: set[str] = set()
    inquiries = summary.get("inquiries") or {}
    for key in ("opened", "resolved", "still_open"):
        for line in inquiries.get(key) or ():
            out.update(_ids((line.get("root_exchange_id"), line.get("question_event_id"))))
    out.update(_ids(summary.get("inquiry_exchanges") or ()))
    for line in summary.get("workbench") or ():
        out.update(_ids((line.get("session_id"), line.get("attempt_id"))))
    for key in ("observations", "predictions_missed"):
        for record in summary.get(key) or ():
            out.update(_ids(record.get("source_event_ids") or ()))
            out.update(_ids((record.get("root_exchange_id"),)))
    for gap in summary.get("gaps_named") or ():
        out.update(_ids((gap.get("gap_id"), gap.get("source_id"))))
    for claim in summary.get("claims_needing_independent_check") or ():
        out.update(_ids(claim.get("attempt_ids") or ()))
    return out


def count_words(text: str) -> int:
    return len(str(text or "").split())


def validate_narrative(answer: ReaderDigestNarrativeV1, summary: Mapping[str, Any]) -> list[str]:
    """Why the narrative cannot stand, or [] (code's check, spec §9.2 / G25):
    the text is non-empty, at most :data:`MAX_WORDS` words and free of the
    well's evidence markers, and it cites at least one id, every one of them
    in the summary."""

    reasons: list[str] = []
    text = str(answer.narrative or "").strip()
    if not text:
        reasons.append("empty")
    if any(marker in text for marker in EVIDENCE_MARKERS):
        # Never a source of a filled mark (round 2 §1): the well's markers are
        # evidence's alone, never in model text about the session.
        reasons.append("evidence_marker")
    words = count_words(text)
    if words > MAX_WORDS:
        reasons.append(f"over_word_cap:{words}")
    cited = [str(value).strip() for value in answer.cited_event_ids]
    if not [value for value in cited if value]:
        reasons.append("no_citations")
    unknown = sorted({value for value in cited if value and value not in citable_ids(summary)})
    if unknown:
        reasons.append("unknown_citations:" + ",".join(unknown))
    return reasons


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        value = str(value).strip()
        if value and value not in out:
            out.append(value)
    return out


# ---------------------------------------------------------------------------
# The prompt (the typed summary and the titles it names; no learner text)
# ---------------------------------------------------------------------------

def _titles(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    los = {lo: vault.learning_objects[lo].title for lo in summary.get("learning_objects_touched") or ()
           if lo in vault.learning_objects}
    sections: dict[str, str] = {}
    extraction_id = str(summary.get("extraction_id") or "")
    wanted = {str(line.get("section_id")) for line in summary.get("sections_read") or () if line.get("section_id")}
    if extraction_id and wanted:
        try:
            labels = RC._sections(repository, extraction_id)
        except Exception:  # noqa: BLE001 - a section list that cannot be read names nothing
            labels = {}
        sections = {section: labels[section] for section in sorted(wanted) if section in labels}
    return {"learning_objects": dict(sorted(los.items())), "sections": sections}


def build_prompt(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> str:
    payload = {
        "task": _INSTRUCTIONS,
        "max_words": MAX_WORDS,
        "summary": dict(summary),
        "titles": _titles(vault, repository, summary),
        "citable_event_ids": sorted(citable_ids(summary)),
    }
    return render_structured_prompt("learnloop reader session narrative", PROMPT_VERSION, payload)


def _anchor_keys(summary: Mapping[str, Any]) -> list[tuple[str, str]]:
    extraction_id = str(summary.get("extraction_id") or "")
    spans: set[str] = set()
    inquiries = summary.get("inquiries") or {}
    for key in ("opened", "resolved", "still_open"):
        for line in inquiries.get(key) or ():
            spans.update(_ids(line.get("span_ids") or ()))
    for key in ("observations", "predictions_missed"):
        for record in summary.get(key) or ():
            spans.update(_ids(record.get("span_ids") or ()))
    return [(extraction_id, span) for span in sorted(spans)] if extraction_id else []


def exam_withheld(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> bool:
    """Whether the session touched a passage the one exam predicate withholds
    (unreadable predicate: withheld, fail closed)."""

    keys = _anchor_keys(summary)
    if not keys:
        return False
    from learnloop.content.sources import exam_material as EM

    try:
        return bool(EM.exam_withheld(vault, repository, keys))
    except Exception:  # noqa: BLE001 - fail closed
        return True


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------

def daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None = None) -> Any:
    from learnloop.source_retrieval.service_spend import SharedDailyEnvelope, midnight

    return SharedDailyEnvelope(vault, repository, day=midnight(clock),
                               cap=float(getattr(_config(vault), "max_daily_cost_usd", 0.0)), clock=clock,
                               name=ENVELOPE, owner_kinds=(OWNER_KIND,),
                               price_per_million=getattr(_config(vault), "price_per_million", None))


def capped_message(vault: Any) -> str:
    return (f"Today's summary budget (${float(getattr(_config(vault), 'max_daily_cost_usd', 0.0)):.2f}) is used. "
            "The lists above are complete without it.")


class NarrativeRoute:
    """The narrative's pinned route for one session."""

    def __init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any,
                 live: Callable[[], None] | None = None) -> None:
        self.vault = vault
        self.repository = repository
        self.injected = client
        self.envelope = envelope
        #: Raises when the session's claim is no longer this worker's (Codex
        #: re-review F3): checked before every attempt's request.
        self.live = live
        self.route: PaidRoute = plan_route(vault, ROUTE_TASK, client)  # type: ignore[arg-type]
        self.client: Any | None = None
        self.calls: PaidCalls | None = None

    @property
    def subscription(self) -> bool:
        return self.route.billing == "subscription"

    @property
    def price(self) -> float | None:
        return getattr(_config(self.vault), "price_per_million", None)

    def problem(self) -> NarrativeUnavailable | None:
        """Checked before any call: the env switch, the route, the price and today's cap."""

        if self.injected is None and models_off():
            return NarrativeUnavailable("models_off", f"{MODELS_ENV}=off: no narrative model is reached.")
        if self.injected is None and not self.route.available:
            return NarrativeUnavailable("unrouted", "No provider is routed for the session narrative "
                                                    "(ai.routing.reader_digest).")
        if not self.subscription and self.price is None:
            return NarrativeUnavailable("unpriced", "A metered narrative route needs digest.price_per_million.")
        if not self.subscription and self.envelope is not None and self.envelope.remaining() <= 0:
            return NarrativeUnavailable("capped", capped_message(self.vault))
        return None

    def ask(self, prompt: str, *, owner_id: str) -> ReaderDigestNarrativeV1:
        problem = self.problem()
        if problem is not None:
            raise problem
        if self.injected is not None:
            self.client = self.injected
        else:
            self.client, message = resolve_client(self.vault, self.route)
            if self.client is None:
                raise NarrativeUnavailable("unavailable", message or "the narrative model is not ready")
        budget = SpendBudget(SpendCaps(max_estimated_usd=None, **_CAPS), subscription=self.subscription)
        live = self.live
        self.calls = PaidCalls(route=self.route, budget=budget, price_per_million=self.price,
                               repository=self.repository, owner_kind=OWNER_KIND, owner_id=owner_id,
                               admit=(lambda _estimate: live()) if live is not None else None)
        with spend_envelopes(self.envelope):
            return self.calls.call(self.client, purpose=PURPOSE, prompt=prompt, result_model=ReaderDigestNarrativeV1,
                                   output_tokens=self.route.output_tokens,
                                   metadata={"prompt_version": PROMPT_VERSION, "digest_id": owner_id})

    @property
    def model(self) -> str:
        if self.calls is not None and self.calls.last_resolved_model:
            return str(self.calls.last_resolved_model)
        return str(getattr(self.client, "model", None) or self.route.model or "unknown")


#: ``judgment_work_claims.task`` of a session's narration (Codex review F3).
CLAIM_TASK = "reader_digest_narrative"


def claim_key(digest_id: str) -> str:
    return f"{CLAIM_TASK}:{digest_id}"


#: Refusals before any call that last only while they hold.
ADMISSION_REASONS = frozenset({"models_off", "unrouted", "unpriced", "capped"})


def admission_problem(vault: Any, repository: Repository, *, client: Any | None = None,
                      clock: Clock | None = None) -> NarrativeUnavailable | None:
    """Whether a narration would be refused now, before any call."""

    route = NarrativeRoute(vault, repository, client=client, envelope=daily_envelope(vault, repository, clock=clock))
    return route.problem()


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

#: The latest transient outcome per (vault, digest) in this process (the
#: plan unavailable, the cap reached, a provider failure): what
#: :func:`narrative_view` shows until the next attempt. Nothing is stored.
_TRANSIENT: dict[tuple[str, str], tuple[str, str | None]] = {}
_TRANSIENT_GUARD = threading.Lock()


def _vault_key(vault: Any) -> str:
    return str(getattr(vault, "root", "") or id(vault))


def _note(vault: Any, digest_id: str, status: str | None, reason: str | None = None) -> None:
    with _TRANSIENT_GUARD:
        if status is None:
            _TRANSIENT.pop((_vault_key(vault), digest_id), None)
        else:
            _TRANSIENT[(_vault_key(vault), digest_id)] = (status, reason)


def _transient(vault: Any, digest_id: str) -> tuple[str, str | None] | None:
    with _TRANSIENT_GUARD:
        return _TRANSIENT.get((_vault_key(vault), digest_id))


def _session_ended(row: Mapping[str, Any], now: datetime) -> bool:
    ended = parse_utc(str(row.get("ended_at") or "")) if row.get("ended_at") else None
    return ended is not None and ended + RS.SESSION_GAP <= now


def _record(repository: Repository, row: Mapping[str, Any], *, narrative: str | None, cited: Sequence[str],
            model: str, prompt: str, reasons: Sequence[str], words: int | None, clock: Clock | None,
            claim: Any | None = None) -> bool:
    """The narrative (or the drop) and its verdict, in one transaction. With
    ``claim``, only while it is still this worker's live lease (checked under
    the write lock; Codex re-review F3): otherwise nothing is written and the
    lease loss is raised. The paid answer stays checkpointed, so the next
    holder lands it without asking again."""

    verdict = "kept" if narrative is not None else "dropped"
    rationale = {"reasons": list(reasons), "cited_event_ids": list(cited), "words": words,
                 "max_words": MAX_WORDS, "narrative_version": NARRATIVE_VERSION, "authority": AUTHORITY}
    with repository.atomic():
        connection = repository.connection()
        if claim is not None:
            from learnloop.hints import map_builder as claims

            if not claims._holds(connection, claim):
                raise claims._LeaseLost("the session's claim lapsed before the narrative was published")
        written = RDG.set_narrative(connection, str(row["id"]), narrative_md=narrative,
                                    cited_event_ids=list(cited) if narrative is not None else None,
                                    model=model, prompt_version=PROMPT_VERSION)
        if written:
            append_judgment(connection, task=LEDGER_TASK, left_kind=LEDGER_LEFT, left_id=str(row["id"]),
                            judge="verifier", judge_model=model, prompt_version=PROMPT_VERSION,
                            input_hash=content_key(prompt or json.dumps(rationale, sort_keys=True)),
                            verdict=verdict, rationale=json.dumps(rationale, sort_keys=True, default=str),
                            created_at=utc_now_iso(clock))
    return written


def narrate_digest(vault: Any, repository: Repository, digest_id: str, *, client: Any | None = None,
                   now: datetime, clock: Clock | None = None) -> NarrativeResult:
    """Write one session's narrative (§9.2), once. Never raises for a model,
    route or spend failure; returns what it did."""

    result = NarrativeResult(status="disabled", digest_id=digest_id)
    if not narrative_enabled(vault):
        return result
    with repository.connection() as connection:
        row = RDG.digest(connection, digest_id)
    if row is None:
        result.status = "no_digest"
        return result
    if row.get("prompt_version"):
        result.status = "already"
        return result
    if not _session_ended(row, now):
        result.status = "not_ended"
        return result
    summary = row.get("summary") or {}
    if exam_withheld(vault, repository, summary):
        _record(repository, row, narrative=None, cited=(), model="none", prompt="", reasons=["exam_material"],
                words=None, clock=clock)
        _note(vault, digest_id, None)
        result.status, result.reasons = "dropped", ["exam_material"]
        return result
    # One durable claim per session before anything is asked (Codex review
    # F3): two sidecars (or a sidecar and a CLI) never pay for the same
    # narrative. The claim is ``judgment_work_claims``' lease and heartbeat
    # (the approach-map builds' and AD's); whoever holds it re-reads the row
    # first. A dead holder's lease lapses and the next Today build retries.
    from learnloop.hints import map_builder as claims

    with claims._claimed(repository, digest_id, 0.0, key=claim_key(digest_id), task=CLAIM_TASK,
                         producer=OWNER_KIND) as claim:
        if claim is None:
            result.status = "claimed"
            return result
        with repository.connection() as connection:
            fresh = RDG.digest(connection, digest_id)
        if fresh is None or fresh.get("prompt_version"):
            result.status = "already"
            return result
        try:
            return _narrate_claimed(vault, repository, row, summary, result, claim, client=client, clock=clock)
        except claims._LeaseLost as exc:
            # Taken over or lapsed (Codex re-review F3): this worker neither
            # sends nor publishes any more; the claim's holder narrates.
            result.status, result.reason = "claimed", str(exc)
            return result


def _narrate_claimed(vault: Any, repository: Repository, row: Mapping[str, Any], summary: Mapping[str, Any],
                     result: NarrativeResult, claim: Any, *, client: Any | None,
                     clock: Clock | None) -> NarrativeResult:
    """The narration itself, under the session's claim (Codex re-review F3).
    The claim's liveness (owner, epoch, unexpired lease) is checked before
    every attempt's request and, under the write lock, at publication; a lost
    claim raises ``_LeaseLost`` and nothing more is sent or written. A paid
    answer is checkpointed before it returns, so whoever holds the claim next
    lands it without a second request. Publication also stays the
    conditional write (``prompt_version IS NULL``): never over another's
    narrative."""

    from learnloop.hints import map_builder as claims

    digest_id = str(row["id"])
    route = NarrativeRoute(vault, repository, client=client, envelope=daily_envelope(vault, repository, clock=clock),
                           live=lambda: claims._require_live(repository, claim))
    prompt = build_prompt(vault, repository, summary)
    try:
        answer = route.ask(prompt, owner_id=digest_id)
    except NarrativeUnavailable as exc:
        result.status, result.reason = exc.reason, exc.message
        _note(vault, digest_id, exc.reason, exc.message)
        return result
    except SpendLimitExceeded as exc:
        result.status, result.reason = "capped", str(exc)
        _note(vault, digest_id, "capped", capped_message(vault))
        return result
    except AIInterrupted:
        raise
    except AIInvalidOutput as exc:
        # Paid for and unusable: dropped, once (never paid for again).
        result.model = route.model
        _record(repository, row, narrative=None, cited=(), model=result.model, prompt=prompt,
                reasons=[f"invalid_output: {exc}"[:300]], words=None, clock=clock, claim=claim)
        _note(vault, digest_id, None)
        result.status, result.reasons = "dropped", ["invalid_output"]
        return result
    except (AIProviderUnavailable, TimeoutError) as exc:
        result.status, result.reason = "failed", f"{type(exc).__name__}: {exc}"[:300]
        _note(vault, digest_id, "failed", result.reason)
        return result
    result.model = route.model
    reasons = validate_narrative(answer, summary)
    text = str(answer.narrative or "").strip()
    cited = _dedupe(answer.cited_event_ids)
    if reasons:
        _record(repository, row, narrative=None, cited=cited, model=result.model, prompt=prompt, reasons=reasons,
                words=count_words(text), clock=clock, claim=claim)
        result.status, result.reasons = "dropped", reasons
    else:
        _record(repository, row, narrative=text, cited=cited, model=result.model, prompt=prompt, reasons=(),
                words=count_words(text), clock=clock, claim=claim)
        result.status = "narrated"
    _note(vault, digest_id, None)
    return result


#: A summary-only digest row's lifecycle marker (Codex review F2): the
#: session's summary was persisted for its narrative while follow-ups were
#: not live, and nothing was planned (``valuation_json.not_planned``, with
#: why). Status ``incomplete``, so follow-ups plan it like any unfinished
#: session once they are live; "planned with no checks" is part 1's
#: ``planned`` row with an empty ``chosen``.
NOT_PLANNED_KEY = "not_planned"


def _not_planned_reason(vault: Any) -> str:
    from learnloop.algorithm_versions import READER_FOLLOWUPS_VERSIONS

    version = getattr(getattr(vault.config, "algorithms", None), "algorithm_version", None)
    return "followups_off" if version in READER_FOLLOWUPS_VERSIONS else "below_followups_successor"


def sessions_to_summarize(vault: Any, repository: Repository, *, now: datetime) -> list[RS.ReaderSession]:
    """Ended reader sessions within follow-ups' time cap with no digest row,
    while narration is on and follow-ups are not live (switched off, or the
    vault below their successor): the narrative's own sessions (Codex review
    F2; ``digest.narrative_enabled`` and ``followups.enabled`` are separate
    switches, §9.6). Cheap: the digests and the session list only; activity
    is checked when a session is summarized. With follow-ups live, part 1
    writes every row and this returns nothing."""

    from datetime import timedelta

    from learnloop.instructional import reader_followups as RF

    if not narrative_enabled(vault) or RF.followups_enabled(vault):
        return []
    horizon = now - timedelta(days=RF.max_wait_days(vault))
    with repository.connection() as connection:
        known = {(row["extraction_id"], row["session_key"]) for row in RDG.digests(connection)}
    out = []
    for session in RS.all_sessions(repository):
        ended = parse_utc(session.ended_at)
        if ended is None or ended + RS.SESSION_GAP > now or ended < horizon:
            continue
        if (session.extraction_id, session.session_id) not in known:
            out.append(session)
    return out


def summarize_ended_sessions(vault: Any, repository: Repository, *, now: datetime,
                             clock: Clock | None = None) -> list[dict[str, Any]]:
    """Persist the typed summary of each session :func:`sessions_to_summarize`
    names and had activity, as a summary-only digest row (``incomplete``,
    ``valuation_json.not_planned``; no commitment, no valuation, no model
    call), so it can be narrated (Codex review F2). A row another process
    wrote meanwhile stands."""

    from learnloop.instructional import reader_followups as RF

    written: list[dict[str, Any]] = []
    reason = _not_planned_reason(vault)
    for session in sessions_to_summarize(vault, repository, now=now):
        summary = RC.session_summary(vault, repository, extraction_id=session.extraction_id, session=session,
                                     now=now)
        if not summary.get("activity"):
            continue
        digest_id = RF.digest_id_for(session.extraction_id, session.session_id)
        stamp = utc_now_iso(clock)
        with repository.atomic():
            connection = repository.connection()
            if RDG.digest_for_session(connection, session.extraction_id, session.session_id) is not None:
                continue
            RDG.insert_digest(connection, {
                "id": digest_id, "extraction_id": session.extraction_id, "session_key": session.session_id,
                "visit_ids": list(session.visit_ids), "started_at": session.started_at,
                "ended_at": session.ended_at, "status": "incomplete", "summary": summary,
                "followup_commitment_ids": [],
                "valuation": {NOT_PLANNED_KEY: reason, "summary_version": summary.get("summary_version"),
                              "questions": [], "chosen": [], "chosen_ids": []},
                "created_at": stamp})
        with repository.connection() as connection:
            row = RDG.digest(connection, digest_id)
        if row is not None:
            written.append(row)
    return written


def digests_waiting(vault: Any, repository: Repository, *, now: datetime, client: Any | None = None,
                    clock: Clock | None = None) -> list[str]:
    """Digest rows whose ended session has no narrative yet, oldest first, or
    [] when narration is switched off or would be refused before any call
    now (so a Today build starts no job that can do nothing). Cheap: reads
    the digests and the route's configuration only."""

    if not narrative_enabled(vault):
        return []
    with repository.connection() as connection:
        rows = RDG.digests(connection)
    waiting = [str(row["id"]) for row in rows if not row.get("prompt_version") and _session_ended(row, now)]
    if not waiting:
        return []
    if admission_problem(vault, repository, client=client, clock=clock) is not None:
        return []
    return waiting


def narrate_waiting(vault: Any, repository: Repository, *, now: datetime, client: Any | None = None,
                    clock: Clock | None = None) -> list[NarrativeResult]:
    """Narrate every waiting session (the background job). Stops at the first
    refusal that holds for every session (no route, no price, the cap)."""

    results = []
    for digest_id in digests_waiting(vault, repository, now=now, client=client, clock=clock):
        result = narrate_digest(vault, repository, digest_id, client=client, now=now, clock=clock)
        results.append(result)
        if result.status in ADMISSION_REASONS | {"unavailable"}:
            break
    return results


# ---------------------------------------------------------------------------
# What the card and Wrap up show (a pure read; W14's states)
# ---------------------------------------------------------------------------

def _landed(row: Mapping[str, Any]) -> dict[str, Any]:
    return {"state": "landed", "digest_id": row["id"], "text": row.get("narrative_md"),
            "cited_event_ids": list(row.get("cited_event_ids") or []), "label": LABEL, "model": row.get("model"),
            "prompt_version": row.get("prompt_version"), "authority": AUTHORITY}


def narrative_view(vault: Any, repository: Repository, *, extraction_id: str, session_key: str | None,
                   now: datetime, client: Any | None = None,
                   clock: Clock | None = None) -> dict[str, Any] | None:
    """The session's narrative for "Last time here" and Wrap up, or None
    (switched off, no digest row for the session yet, or the session still
    running).

    ``state``: ``landed`` (the text, its cited ids, the label), ``failed``
    (dropped once, never retried), ``capped`` (today's metered cap; the
    message names it), ``unreachable`` (the model could not be reached or the
    route cannot run; retried at the next Today build) or ``pending``."""

    if not narrative_enabled(vault) or not session_key:
        return None
    with repository.connection() as connection:
        row = RDG.digest_for_session(connection, extraction_id, session_key)
    base = {"label": LABEL, "authority": AUTHORITY, "narrative_version": NARRATIVE_VERSION}
    if row is None:
        # Part 1 writes the row at the first Today build after a session with
        # activity ends; until then (and for a session with no activity, or
        # one still running) there is no narrative to show or wait for.
        return None
    if row.get("prompt_version"):
        if row.get("narrative_md"):
            return {**base, **_landed(row)}
        return {**base, "state": "failed", "digest_id": row["id"],
                "message": "LearnLoop's model couldn't write a summary of this session that matched what you did."}
    if not _session_ended(row, now):
        return None
    problem = admission_problem(vault, repository, client=client, clock=clock)
    if problem is not None and problem.reason == "capped":
        return {**base, "state": "capped", "digest_id": row["id"], "message": problem.message,
                "cap_usd": float(getattr(_config(vault), "max_daily_cost_usd", 0.0))}
    if problem is not None:
        return {**base, "state": "unreachable", "digest_id": row["id"], "reason": problem.reason,
                "message": problem.message}
    noted = _transient(vault, str(row["id"]))
    if noted is not None and noted[0] == "capped":
        return {**base, "state": "capped", "digest_id": row["id"], "message": noted[1] or capped_message(vault),
                "cap_usd": float(getattr(_config(vault), "max_daily_cost_usd", 0.0))}
    if noted is not None:
        return {**base, "state": "unreachable", "digest_id": row["id"], "reason": noted[0], "message": noted[1]}
    return {**base, "state": "pending", "digest_id": row["id"]}


__all__ = [
    "ADMISSION_REASONS",
    "AUTHORITY",
    "LABEL",
    "LEDGER_TASK",
    "MAX_WORDS",
    "NarrativeResult",
    "NarrativeRoute",
    "PROMPT_VERSION",
    "ROUTE_TASK",
    "ReaderDigestNarrativeV1",
    "admission_problem",
    "build_prompt",
    "citable_ids",
    "count_words",
    "digest_enabled",
    "digests_waiting",
    "narrate_digest",
    "narrate_waiting",
    "narrative_enabled",
    "narrative_view",
    "sessions_to_summarize",
    "summarize_ended_sessions",
    "validate_narrative",
]
