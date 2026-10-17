"""Reader quick-check producer: AI-authored section-boundary questions.

The producer half of the mnemonic-medium boundary prompt: as the learner
approaches the end of a section while reading closely, a durable
``reader_quick_check`` job authors ONE span-grounded comprehension question for
that section (codex ``run_reading_quick_check``, getattr-discovered), validated
in code against the section's own spans and persisted as a
``reader_authored_questions`` row.  The guide plan surfaces it only where no
owner-reviewed placement exists (``placement: auto_authored``).

Evidence honesty: an authored question has no practice item, surface, or
administration.  Answering it is a formative self-check recorded on the row
(never attempts/mastery).  The learner may escalate it into a real
PracticeItem — the Matuschak reader-control act of collecting a prompt — which
mints a learner-authority card with ``codex_proposal`` provenance and
``span:<extraction_id>/<span_id>`` source refs.
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.execution import (
    content_key,
    generation_limit,
    observe_model_calls,
    requested_reasoning_effort,
    single_request,
)
from learnloop.ai.output_budget import TruncationRetry, output_budget, output_ceiling, reasoning_effort
from learnloop.ai.spend import (
    SpendBudget,
    SpendCaps,
    SpendEstimate,
    SpendLimitExceeded,
    is_subscription_transport,
    subscription_usage_estimate,
)
from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.config.schema import DEFAULT_OUTPUT_TOKENS
from learnloop.reader.ai_contracts import (
    ACTIVE_QUESTION_STYLES,
    READING_ACTIVE_PROMPT_VERSION,
    READING_PASSAGE_CHECK_PROMPT_VERSION,
    ReadingActiveCheck,
    ReadingActiveContext,
    ReadingQuickCheck,
    ReadingQuickCheckContext,
    reading_active_prompt,
    reading_passage_check_prompt,
    reading_quick_check_prompt,
)
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgment_claims import (
    CLAIMED,
    DONE,
    HELD,
    claim_work,
    complete_claim,
    holds_claim,
    lease_holder,
    release_claim,
    take_over_claim,
)
from learnloop.db.stores.judgments import append_judgment
from learnloop.ids import new_ulid
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span
from learnloop.reader.reader_guidance import extraction_sections
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

# Keep the authoring context bounded: a pathological "section" (e.g. the
# whole-source fallback unit) is truncated, never silently expanded.
MAX_SECTION_BLOCKS = 60
MAX_SECTION_CHARS = 24_000

QUESTION_ACTIONS = ("answered", "dismissed")

# RW1a: the reconnect line's passage-scoped check (spec_reader_workbench_v1 §4.1).
# The passage is the inquiry's anchor plus a little context on each side,
# inside the anchor's section (the producer never reads past it).
INQUIRY_PROMPT_VERSION = READING_PASSAGE_CHECK_PROMPT_VERSION
PASSAGE_BLOCKS_BEFORE = 1
PASSAGE_BLOCKS_AFTER = 2
MAX_PASSAGE_CHARS = 8_000
INQUIRY_ACTIONS = ("answered", "self_checked", "dismissed")
SELF_CHECKS = ("matches", "partly", "no")

# The passage check's paid call (W10; Codex review F1-F3). Its receipts are
# owned by this kind (the daily count reads them); its reuse key is claimed
# durably before the call (judgment_work_claims, the shared work-claim table)
# so two workers never pay for, or land, two checks for one inquiry.
PASSAGE_CHECK_RECEIPT_OWNER = "reader_inquiry_check"
INQUIRY_CLAIM_TASK = "reader_inquiry_check"
INQUIRY_CLAIM_PRODUCER = "reader_quick_check"
# Longer than any one call (the Codex turn timeout is 8 minutes): a live
# worker is never taken over; a crashed one is after this long, or at once by
# its own job when the runner re-runs it.
INQUIRY_CLAIM_LEASE_SECONDS = 30 * 60
# Prompt-size bound of one passage check (the passage is at most
# MAX_PASSAGE_CHARS, about 2,000 tokens, plus the envelope).
PASSAGE_CHECK_PROMPT_TOKENS = 8_000
# The passage check's route: its client (the inventory resolver), its output
# budget and its reasoning effort under the shared policy.
PASSAGE_CHECK_ROUTE = "canonical_ingest"
PASSAGE_CHECK_PURPOSE = "reading_quick_check"
# The learner's own verdict after comparing answers (W10: every learner-card
# verdict appends to judgment_ledger).
SELF_CHECK_TASK = "reader_quick_check_self_check"


class ReaderQuickCheckError(ValueError):
    """Domain error for the reader quick-check producer."""


class PassageCheckRefused(ReaderQuickCheckError):
    """The spend framework refused the passage check before anything was sent.

    ``reason`` is ``capped`` (today's checks are used) or ``spend_refused``.
    A ``spend_refused`` names its ``refusal`` (re-review F15): ``no_price`` (a
    metered route with no owner price) or ``over_cap`` (the estimate is over
    the per-check cap), so the learner is told the right one."""

    def __init__(self, reason: str, message: str, *, refusal: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.refusal = refusal


class InquiryCheckHeld(ReaderQuickCheckError):
    """Another worker holds this inquiry's claim: no call was made."""


@dataclass(frozen=True)
class PassageCheckSpend:
    """Admission settings of one passage check (``[reader_inquiry]``, W10).

    ``max_checks_per_day`` counts the check's root receipts since UTC midnight
    (failed calls included, a truncation retry too; None: no daily count). A
    metered route is priced at ``price_per_million`` (None: refused before
    sending) and held to ``max_usd_per_check`` and to one admitted request per
    physical request. ``output_tokens`` is the route's budget under the
    shared output-budget policy (``learnloop.ai.output_budget``): the output
    limit of a metered request, a prompt hint on the subscription, and the
    reservation; a truncation is retried once at double it (admitted like any
    retry), never accepted. ``reasoning_effort`` is the route's
    (``ai.route_reasoning_effort``; None keeps the profile's). A subscription
    route (Codex, the ChatGPT plan) is estimated_only, with no token, dollar
    or physical-request bound."""

    max_checks_per_day: int | None = 100
    max_usd_per_check: float = 0.25
    price_per_million: float | None = None
    output_tokens: int = DEFAULT_OUTPUT_TOKENS
    cancelled: Callable[[], bool] | None = None
    reasoning_effort: str | None = None

    def caps(self) -> SpendCaps:
        # One call and one truncation retry at twice the output budget.
        return SpendCaps(
            max_candidates=1, max_pairs=0, max_retries=1, max_calls=2,
            max_total_tokens=PASSAGE_CHECK_PROMPT_TOKENS * 2 + self.output_tokens * 3,
            max_estimated_usd=self.max_usd_per_check,
        )


def passage_check_spend(
    config: Any, *, provider: str | None = None, cancelled: Callable[[], bool] | None = None,
) -> PassageCheckSpend:
    """The vault's passage-check admission settings (``[reader_inquiry]``,
    and the shared output-budget policy for the check's route: its budget and
    its reasoning effort)."""

    settings = config.reader_inquiry
    return PassageCheckSpend(
        max_checks_per_day=int(settings.max_checks_per_day),
        max_usd_per_check=float(settings.max_usd_per_check),
        price_per_million=settings.metered_price_per_million,
        output_tokens=int(output_budget(config, PASSAGE_CHECK_ROUTE, provider=provider)),
        cancelled=cancelled,
        reasoning_effort=reasoning_effort(config, PASSAGE_CHECK_ROUTE),
    )


def inquiry_claim_key(inquiry_root_event_id: str, prompt_version: str | None = None) -> str:
    return f"{INQUIRY_CLAIM_TASK}:{prompt_version or INQUIRY_PROMPT_VERSION}:{inquiry_root_event_id}"


def _estimate_tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4


def request_reading_quick_check(
    client: StructuredTransport, context: ReadingQuickCheckContext
) -> ReadingQuickCheck:
    """Author one section quick check through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="reading_quick_check",
        prompt=reading_quick_check_prompt(context),
        result_model=ReadingQuickCheck,
    )


def request_passage_check(
    client: StructuredTransport, context: ReadingQuickCheckContext
) -> ReadingQuickCheck:
    """Author one passage-scoped quick check (RW1a) through the shared transport.

    The same operation and contract as the section check (only the prompt says
    "passage"), but the passage is untrusted source text: the request is an
    isolated turn (no files, shell, network, connectors or vault), and a
    transport that cannot isolate it is refused before any request
    (``AIProviderUnavailable``). Spend admission is the caller's
    (:func:`author_inquiry_quick_check`)."""

    return execute_structured_operation(
        client,
        purpose=PASSAGE_CHECK_PURPOSE,
        prompt=reading_passage_check_prompt(context),
        result_model=ReadingQuickCheck,
        isolated=True,
    )


def _admitted_passage_check(
    repository: Repository,
    client: Any,
    context: Any,
    *,
    spend: PassageCheckSpend,
    owner_id: str,
    clock: Clock | None,
    prompt: Callable[[Any], str] = reading_passage_check_prompt,
    request: Callable[[Any, Any], Any] = request_passage_check,
) -> Any:
    """Admit one passage check through the spend framework, then send it.

    Refused (``PassageCheckRefused``) before anything is sent when today's
    checks are used, or on a metered route without a price or over the
    per-check cap. Every receipt (owner ``PASSAGE_CHECK_RECEIPT_OWNER``) is
    written before its request, so a failed call still counts toward the day.

    The daily count is reserved atomically (re-review F2): the root receipt is
    written in the same write transaction that counts the day's receipts, so
    two workers (different inquiries, one slot left) can never both read
    spare capacity and both send. The count up front is only a fast path
    that skips building the request when the day is plainly used.

    The shared output-budget policy (``learnloop.ai.output_budget``): every
    attempt asks for the route's budget (the output limit of a metered
    request, a prompt hint on the subscription) and reasoning effort. A
    truncated answer is never accepted: it is logged and retried once at
    double the budget (held to the transport's ceiling), the retry admitted
    like any other attempt (the per-check caps, the day's count) and tagged
    on its receipt; a second truncation, or one at the ceiling, fails."""

    day = parse_utc(utc_now_iso(clock)).strftime("%Y-%m-%d")
    limit = spend.max_checks_per_day

    def capped() -> PassageCheckRefused:
        return PassageCheckRefused("capped", f"Today's quick checks ({limit}) are used.")

    if limit is not None and repository.model_call_roots_since(
        owner_kind=PASSAGE_CHECK_RECEIPT_OWNER, since=day
    ) >= limit:
        raise capped()
    subscription = is_subscription_transport(client=client)
    prompt_tokens = _estimate_tokens(prompt(context))
    price = spend.price_per_million
    if price is None and not subscription:
        raise PassageCheckRefused(
            "spend_refused",
            "The quick check was refused before sending: no price is set for this metered model.",
            refusal="no_price",
        )
    budget = SpendBudget(spend.caps(), cancelled=spend.cancelled, subscription=subscription)
    truncation = TruncationRetry(
        spend.output_tokens, role=PASSAGE_CHECK_PURPOSE, provider=getattr(client, "provider_name", None),
        model=getattr(client, "model", None), owner_kind=PASSAGE_CHECK_RECEIPT_OWNER, owner_id=owner_id,
        ceiling=output_ceiling(client),
    )
    while True:
        retry = truncation.retried
        planned = prompt_tokens + truncation.budget
        estimate = SpendEstimate(
            candidates=0 if retry else 1, calls=1, retries=1 if retry else 0, total_tokens=planned,
            estimated_usd=(planned * price / 1_000_000) if price is not None else None,
        )
        try:
            budget.check(estimate)
        except SpendLimitExceeded as exc:
            what = (
                f"its answer was cut off and the retry at {truncation.budget} output tokens was refused"
                if retry else "the quick check was refused"
            )
            raise PassageCheckRefused(
                "spend_refused", f"{what[0].upper()}{what[1:]} before sending: {exc}.", refusal="over_cap",
            ) from exc
        try:
            return _send_passage_check(
                repository, client, context, budget=budget, estimate=estimate, planned=planned,
                price=price, subscription=subscription, limit=limit, day=day, capped=capped,
                owner_id=owner_id, output_tokens=truncation.budget, truncation=truncation,
                effort=spend.reasoning_effort, request=request,
            )
        except AIOutputTruncated:
            if not truncation.after_truncation(allowed=budget.used.retries < budget.caps.max_retries):
                raise


def _send_passage_check(
    repository: Repository,
    client: Any,
    context: ReadingQuickCheckContext,
    *,
    budget: SpendBudget,
    estimate: SpendEstimate,
    planned: int,
    price: float | None,
    subscription: bool,
    limit: int | None,
    day: str,
    capped: Callable[[], PassageCheckRefused],
    owner_id: str,
    output_tokens: int,
    truncation: TruncationRetry,
    effort: str | None,
    request: Callable[[Any, Any], Any] = request_passage_check,
) -> Any:
    """One admitted attempt of the passage check: its receipts, its request."""

    totals: dict[str, Any] = {"input": 0, "output": 0, "cost": None, "root": None}
    refused: list[PassageCheckRefused] = []

    def receipt(action: str, event: dict[str, Any]) -> None:
        if action == "start" and event.get("parent_call_id") is None and limit is not None:
            # Count and reserve in one write transaction: raising here stops
            # the call before its request is sent, with no receipt written.
            with repository.atomic():
                if repository.model_call_roots_since(owner_kind=PASSAGE_CHECK_RECEIPT_OWNER, since=day) >= limit:
                    refused.append(capped())
                    raise refused[-1]
                repository.record_model_event(
                    action, event, owner_kind=PASSAGE_CHECK_RECEIPT_OWNER, owner_id=owner_id
                )
            totals["root"] = event.get("id")
            return
        if action == "start" and event.get("parent_call_id") is None:
            totals["root"] = event.get("id")
        if action == "finish":
            totals["input"] += int(event.get("input_tokens") or 0)
            totals["output"] += int(event.get("output_tokens") or 0)
            if isinstance(event.get("cost"), (int, float)):
                totals["cost"] = (totals["cost"] or 0.0) + float(event["cost"])
            if subscription:
                # estimated_only (Slice A §5 rule 6): from reported usage (the
                # root sums its physical requests), else the planned estimate.
                basis = (
                    {"input_tokens": totals["input"], "output_tokens": totals["output"]}
                    if event.get("id") == totals["root"] else event
                )
                event = {**event, "usage_json": json.dumps({
                    **json.loads(event.get("usage_json") or "{}"),
                    **subscription_usage_estimate(
                        basis, planned_tokens=planned,
                        price_per_token=(price / 1_000_000) if price is not None else None,
                    ),
                }, sort_keys=True)}
        repository.record_model_event(action, event, owner_kind=PASSAGE_CHECK_RECEIPT_OWNER, owner_id=owner_id)

    with budget.request(estimate) as charge:
        try:
            with ExitStack() as stack:
                stack.enter_context(observe_model_calls(receipt))
                if not subscription:
                    # Metered: the one admitted request is the only physical
                    # request (no hidden retry or repair).
                    stack.enter_context(single_request())
                # The route's budget: a metered request's output limit, a
                # prompt hint on the subscription (no output cap is sent).
                stack.enter_context(generation_limit(output_tokens))
                stack.enter_context(truncation.receipts())
                stack.enter_context(requested_reasoning_effort(effort))
                return request(client, context)
        except BaseException:
            if refused:
                raise refused[0] from None
            raise
        finally:
            if not subscription:
                reported = totals["input"] + totals["output"]
                cost = totals["cost"]
                if cost is None and reported and price is not None:
                    cost = reported * price / 1_000_000
                charge.reconcile(total_tokens=reported or None, estimated_usd=cost)


def section_view(repository: Repository, *, extraction_id: str, section_id: str) -> dict[str, Any]:
    """The bounded, readable view of ONE guide section: {section_id, label,
    blocks:[{span_id, kind, text}]}. Uses the same section derivation as the
    guide plan so producer and consumer agree on boundaries."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderQuickCheckError(f"extraction has no IR: {extraction_id!r}")
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)
    section = next((row for row in section_rows if row["id"] == section_id), None)
    if section is None:
        raise ReaderQuickCheckError(f"unknown section: {section_id!r}")

    blocks: list[dict[str, str]] = []
    total_chars = 0
    for span_id in section["span_ids"][:MAX_SECTION_BLOCKS]:
        block = block_by_span[span_id]
        text = " ".join((block.text or "").split())
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_SECTION_CHARS:
            break
        blocks.append({"span_id": span_id, "kind": str(block.block_type or ""), "text": text})
    if not blocks:
        raise ReaderQuickCheckError(f"section has no readable text: {section_id!r}")
    return {"section_id": section["id"], "label": section["label"], "blocks": blocks}


def author_quick_check(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    section_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author + persist one quick check for a section (idempotent).

    Any existing row for the section is reused — a ``dismissed`` newest row is
    the learner's durable "don't bring this back" and suppresses re-authoring.
    The model output is candidate-only: span citations are validated against
    the section's provided spans before anything is persisted."""

    existing = repository.latest_reader_authored_question(
        extraction_id=extraction_id, section_id=section_id
    )
    if existing is not None:
        return existing

    view = section_view(repository, extraction_id=extraction_id, section_id=section_id)

    from learnloop.reader.ai_contracts import READING_QUICK_CHECK_PROMPT_VERSION

    result = request_reading_quick_check(
        client,
        ReadingQuickCheckContext(extraction_id=extraction_id, section=view)
    )
    question_md = (result.question_md or "").strip()
    expected_answer_md = (result.expected_answer_md or "").strip()
    if not question_md or not expected_answer_md:
        raise ReaderQuickCheckError("the model returned an empty question or answer")
    valid_spans = {block["span_id"] for block in view["blocks"]}
    span_ids = [span_id for span_id in result.span_ids if span_id in valid_spans]
    if not span_ids:
        raise ReaderQuickCheckError(
            f"the model cited no valid section spans: {list(result.span_ids)!r}"
        )

    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    question_id = repository.insert_reader_authored_question(
        fields={
            "extraction_id": extraction_id,
            "section_id": section_id,
            "source_id": revision.get("source_id"),
            "question_md": question_md,
            "expected_answer_md": expected_answer_md,
            "span_ids": span_ids,
            "prompt_version": READING_QUICK_CHECK_PROMPT_VERSION,
            "provider": getattr(getattr(client, "config", None), "provider", None)
            or getattr(client, "provider_name", None),
            "model": getattr(getattr(client, "config", None), "model", None)
            or getattr(client, "model", None),
        },
        clock=clock,
    )
    row = repository.get_reader_authored_question(question_id)
    assert row is not None
    return row


def passage_view(
    repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...]
) -> dict[str, Any]:
    """The bounded view of one inquiry's root passage (RW1a): its anchor spans
    and up to ``PASSAGE_BLOCKS_BEFORE``/``AFTER`` neighbours, inside the anchor's
    guide section (the same section derivation as the guide plan).

    ``{section_id, label, scope: "passage", anchor_span_ids, blocks}``."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderQuickCheckError(f"extraction has no IR: {extraction_id!r}")
    section_rows, block_by_span, span_to_section = extraction_sections(ir)
    anchors = [span_id for span_id in dict.fromkeys(anchor_span_ids) if span_id in span_to_section]
    if not anchors:
        raise ReaderQuickCheckError(f"the passage has no readable anchor: {list(anchor_span_ids)!r}")
    section_id = span_to_section[anchors[0]]
    section = next(row for row in section_rows if row["id"] == section_id)
    order = list(section["span_ids"])
    anchors = [span_id for span_id in anchors if span_id in order]
    positions = [order.index(span_id) for span_id in anchors]
    window = order[max(0, min(positions) - PASSAGE_BLOCKS_BEFORE):max(positions) + 1 + PASSAGE_BLOCKS_AFTER]
    blocks: list[dict[str, str]] = []
    total_chars = 0
    for span_id in window:
        block = block_by_span[span_id]
        text = " ".join((block.text or "").split())
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_PASSAGE_CHARS and span_id not in anchors:
            continue
        blocks.append({"span_id": span_id, "kind": str(block.block_type or ""), "text": text})
    if not any(block["span_id"] in anchors for block in blocks):
        raise ReaderQuickCheckError("the passage has no readable text")
    return {
        "section_id": section_id,
        "label": section["label"],
        "scope": "passage",
        "anchor_span_ids": anchors,
        "blocks": blocks,
    }


def author_inquiry_quick_check(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    inquiry_root_event_id: str,
    anchor_span_ids: list[str] | tuple[str, ...],
    clock: Clock | None = None,
    spend: PassageCheckSpend | None = None,
    owner: str | None = None,
    owner_ended: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Author + persist the reconnect line's quick check for one inquiry (RW1a).

    One check per (``inquiry_root_event_id``, prompt version): any existing
    row is reused, a dismissed one included, and the key is claimed durably
    before the model call (``owner``: the claiming job; a live claim held by
    another owner raises ``InquiryCheckHeld`` with no call made; an expired
    one, or the same owner's after a crash, is taken over). A claim whose
    owner has ended is taken over at once, before its lease runs out, when
    ``owner_ended(holder)`` says so (re-review F13: the job that claimed it
    is terminal, so it will never land or release it). The row lands
    only while the claim still holds, and the database refuses a second row
    for the key, so a late completion never replaces the check the learner
    saw. The call is admitted through ``spend`` first (W10; default: no
    price, so a metered route is refused) and sent as an isolated turn.
    Formative only (W1 tier 2): the row is the record, answering it writes no
    attempt. Span citations are validated against the passage before
    anything is persisted."""

    existing = repository.inquiry_reader_authored_question(
        inquiry_root_event_id=inquiry_root_event_id, prompt_version=INQUIRY_PROMPT_VERSION
    )
    if existing is not None:
        return existing

    owner = owner or f"inline_{new_ulid()}"
    spend = spend if spend is not None else PassageCheckSpend()
    key = inquiry_claim_key(inquiry_root_event_id)

    def claim(*, rerun: bool = False) -> tuple[str, int | None]:
        now = utc_now_iso(clock)
        with repository.atomic():
            connection = repository.connection()
            state, epoch = claim_work(
                connection, claim_key=key, task=INQUIRY_CLAIM_TASK,
                producer=INQUIRY_CLAIM_PRODUCER, prompt_version=INQUIRY_PROMPT_VERSION,
                input_hash=content_key([inquiry_root_event_id, list(anchor_span_ids)]),
                owner=owner, now=now, lease_seconds=INQUIRY_CLAIM_LEASE_SECONDS,
                rerun=rerun,
            )
            if state == HELD and owner_ended is not None:
                holder = lease_holder(connection, claim_key=key)
                if holder is not None and owner_ended(holder):
                    epoch = take_over_claim(
                        connection, claim_key=key, from_owner=holder, owner=owner, now=now,
                        lease_seconds=INQUIRY_CLAIM_LEASE_SECONDS,
                    )
                    state = CLAIMED if epoch is not None else HELD
            return state, epoch

    state, epoch = claim()
    if state == DONE:
        landed = repository.inquiry_reader_authored_question(
            inquiry_root_event_id=inquiry_root_event_id, prompt_version=INQUIRY_PROMPT_VERSION
        )
        if landed is not None:
            return landed
        state, epoch = claim(rerun=True)  # a finished claim whose row is gone
    if state == HELD or epoch is None:
        raise InquiryCheckHeld("Another worker is writing this quick check.")

    try:
        view = passage_view(repository, extraction_id=extraction_id, anchor_span_ids=anchor_span_ids)
        result = _admitted_passage_check(
            repository, client, ReadingQuickCheckContext(extraction_id=extraction_id, section=view),
            spend=spend, owner_id=inquiry_root_event_id, clock=clock,
        )
        question_md = (result.question_md or "").strip()
        expected_answer_md = (result.expected_answer_md or "").strip()
        if not question_md or not expected_answer_md:
            raise ReaderQuickCheckError("the model returned an empty question or answer")
        valid_spans = {block["span_id"] for block in view["blocks"]}
        span_ids = [span_id for span_id in result.span_ids if span_id in valid_spans]
        if not span_ids:
            raise ReaderQuickCheckError(
                f"the model cited no valid passage spans: {list(result.span_ids)!r}"
            )
    except BaseException:
        # Nothing landed: give the key back so the next request may take it.
        with repository.atomic():
            release_claim(repository.connection(), claim_key=key, owner=owner, epoch=epoch,
                          now=utc_now_iso(clock))
        raise

    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    question_id: str | None = None
    with repository.atomic():
        connection = repository.connection()
        if holds_claim(connection, claim_key=key, owner=owner, epoch=epoch):
            question_id = _insert_inquiry_row(
                repository, client, extraction_id=extraction_id, view=view, revision=revision,
                question_md=question_md, expected_answer_md=expected_answer_md, span_ids=span_ids,
                inquiry_root_event_id=inquiry_root_event_id, clock=clock,
            )
            complete_claim(connection, claim_key=key, owner=owner, epoch=epoch,
                           judgment_id=question_id, now=utc_now_iso(clock))
    if question_id is None:
        # Fenced out: another worker took the key over while this call ran.
        landed = repository.inquiry_reader_authored_question(
            inquiry_root_event_id=inquiry_root_event_id, prompt_version=INQUIRY_PROMPT_VERSION
        )
        if landed is not None:
            return landed
        raise InquiryCheckHeld("Another worker took this quick check over.")
    row = repository.get_reader_authored_question(question_id)
    assert row is not None
    return row


def _insert_inquiry_row(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    view: dict[str, Any],
    revision: dict[str, Any],
    question_md: str,
    expected_answer_md: str,
    span_ids: list[str],
    inquiry_root_event_id: str,
    clock: Clock | None,
) -> str:
    return repository.insert_reader_authored_question(
        fields={
            "extraction_id": extraction_id,
            "section_id": view["section_id"],
            "source_id": revision.get("source_id"),
            "question_md": question_md,
            "expected_answer_md": expected_answer_md,
            "span_ids": span_ids,
            "prompt_version": INQUIRY_PROMPT_VERSION,
            "provider": getattr(getattr(client, "config", None), "provider", None)
            or getattr(client, "provider_name", None),
            "model": getattr(getattr(client, "config", None), "model", None)
            or getattr(client, "model", None),
            "scope_kind": "inquiry",
            "question_style": "recall",
            "anchor_span_ids": view["anchor_span_ids"],
            "inquiry_root_event_id": inquiry_root_event_id,
        },
        clock=clock,
    )


def record_inquiry_action(
    repository: Repository,
    *,
    question_id: str,
    action: str,
    response_md: str | None = None,
    self_check: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's act on an inquiry-scoped quick check (RW1a).

    ``answered`` stamps their response (the expected answer is then shown
    beside it); ``self_checked`` records their own verdict -- matches, partly
    or no -- in ``self_check`` and, in the same transaction, appends it to
    ``judgment_ledger`` as a ``learner_card`` verdict on (question, response)
    (W10): a changed verdict supersedes the previous one, so the history stays
    auditable for later calibration, and repeating a verdict appends nothing.
    ``dismissed`` is the durable "don't bring this back". Formative only: no
    attempt, observation, mastery or FSRS row. A "partly" or "no" becomes
    reader_formative learner text in RW1b, not here."""

    if action not in INQUIRY_ACTIONS:
        raise ReaderQuickCheckError(f"unknown question action: {action!r}")
    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row.get("scope_kind") != "inquiry":
        raise ReaderQuickCheckError("not an inquiry quick check")
    if row["status"] == "escalated":
        raise ReaderQuickCheckError("this question was already added to practice")
    if action == "self_checked":
        if self_check not in SELF_CHECKS:
            raise ReaderQuickCheckError(f"unknown self-check: {self_check!r}")
        if row["status"] != "answered":
            raise ReaderQuickCheckError("answer the question before comparing")
        with repository.atomic():
            repository.transition_reader_authored_question(
                question_id=question_id, status="answered", self_check=self_check, clock=clock
            )
            _append_self_check_verdict(repository, row, self_check, clock=clock)
    elif action == "answered":
        response = (response_md or "").strip()
        if not response:
            raise ReaderQuickCheckError("an answer is needed to compare with the source")
        repository.transition_reader_authored_question(
            question_id=question_id, status="answered", response_md=response, clock=clock
        )
    else:
        repository.transition_reader_authored_question(
            question_id=question_id, status="dismissed", clock=clock
        )
    refreshed = repository.get_reader_authored_question(question_id)
    assert refreshed is not None
    return refreshed


def _append_self_check_verdict(
    repository: Repository, row: dict[str, Any], verdict: str, *, clock: Clock | None
) -> str | None:
    """Append the learner's self-check to ``judgment_ledger`` (inside the
    caller's transaction). The question is (authored question, the response
    it judges): an answer rewritten later is a new question. Idempotent: the
    same verdict as the current one appends nothing; a different one
    supersedes it, with an id derived from the transition so a retried
    request never appends twice. Returns the appended id, or None."""

    question_id = str(row["id"])
    response_key = content_key([question_id, row.get("response_md") or "", row.get("answered_at") or ""])[:32]
    connection = repository.connection()
    rows = connection.execute(
        "SELECT id, verdict, supersedes_id FROM judgment_ledger WHERE task = ? AND left_kind = ? "
        "AND left_id = ? AND right_kind = ? AND right_id = ?",
        (SELF_CHECK_TASK, "reader_authored_question", question_id, "reader_quick_check_response", response_key),
    ).fetchall()
    superseded = {r[2] for r in rows if r[2]}
    current = next((r for r in rows if r[0] not in superseded), None)
    if current is not None and current[1] == verdict:
        return None
    judgment_id = "rqcsc_" + content_key([question_id, response_key, verdict, current[0] if current else None])[:40]
    if any(r[0] == judgment_id for r in rows):
        return None
    return append_judgment(
        connection,
        id=judgment_id,
        task=SELF_CHECK_TASK,
        left_kind="reader_authored_question",
        left_id=question_id,
        right_kind="reader_quick_check_response",
        right_id=response_key,
        judge="learner_card",
        input_hash=content_key({
            "question_md": row.get("question_md"),
            "expected_answer_md": row.get("expected_answer_md"),
            "response_md": row.get("response_md"),
        }),
        verdict=verdict,
        prompt_version=row.get("prompt_version"),
        rationale="the learner compared their answer with the quick check's intended answer",
        supersedes_id=current[0] if current else None,
        created_at=utc_now_iso(clock),
    )


def record_action(
    repository: Repository,
    *,
    question_id: str,
    action: str,
    response_md: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's self-check outcome on the row (salience-only):
    ``answered`` stamps their response; ``dismissed`` is the durable
    "don't bring this back"."""

    if action not in QUESTION_ACTIONS:
        raise ReaderQuickCheckError(f"unknown question action: {action!r}")
    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row["status"] == "escalated":
        raise ReaderQuickCheckError("this question was already added to practice")
    repository.transition_reader_authored_question(
        question_id=question_id,
        status=action,
        response_md=(response_md or "").strip() or None,
        clock=clock,
    )
    refreshed = repository.get_reader_authored_question(question_id)
    assert refreshed is not None
    return refreshed


def escalate(
    root: Path,
    repository: Repository,
    *,
    question_id: str,
    learning_object_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Escalate an authored quick check into a real PracticeItem.

    A learner-authority write (no review gate — the learner collecting a
    prompt is the authority, per the Matuschak reader-control slice), but the
    provenance stays honest: ``origin="codex_proposal"`` with the question's
    span refs, so the card never masquerades as human-authored."""

    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row["status"] == "escalated":
        return {"practice_item_id": row["practice_item_id"], "question": row}
    if row["status"] == "dismissed":
        raise ReaderQuickCheckError("a dismissed question cannot be added to practice")

    vault = load_vault(root)
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise ReaderQuickCheckError(f"unknown learning object {learning_object_id!r}")

    try:
        span_ids = json.loads(row.get("span_ids_json") or "[]")
    except (TypeError, json.JSONDecodeError):
        span_ids = []
    source_refs = [
        {
            "ref_type": "canonical_source",
            "ref_id": str(row.get("source_id") or row["extraction_id"]),
            "locator": format_block_span(row["extraction_id"], str(span_id)),
            "locator_scheme": BLOCK_SPAN_V1,
        }
        for span_id in span_ids
        if isinstance(span_id, str)
    ]
    now = utc_now_iso(clock)
    item_id = f"pi_reader_{new_ulid().lower()}"
    payload: dict[str, Any] = {
        "id": item_id,
        "learning_object_id": learning_object_id,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": [],
        "prompt": str(row["question_md"]),
        "expected_answer": str(row["expected_answer_md"]),
        "hints": [],
        # A card must always be gradable: same plain correctness rubric as
        # learner-authored cards, so grading never depends on a vault default.
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {
                    "id": "correctness",
                    "points": 4,
                    "description": "Answer matches the expected answer in substance.",
                }
            ],
        },
        "provenance": {"origin": "codex_proposal", "source_refs": source_refs},
        "created_at": now,
        "updated_at": now,
    }
    upsert_practice_item(root, payload, clock=clock)
    repository.transition_reader_authored_question(
        question_id=question_id, status="escalated", practice_item_id=item_id, clock=clock
    )
    try:
        repository.append_interaction_event(
            kind="learner_item_authored",
            origin="learner",
            subject_type="practice_item",
            subject_id=item_id,
            payload_json=json.dumps(
                {
                    "learning_object_id": learning_object_id,
                    "escalated_from": question_id,
                    "mechanism": "reader_quick_check_escalation",
                },
                sort_keys=True,
            ),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - provenance trail is best-effort
        pass
    refreshed = repository.get_reader_authored_question(question_id)
    return {"practice_item_id": item_id, "question": refreshed or row}


# ---------------------------------------------------------------------------
# RW1b: active reading on a selection (spec_reader_workbench_v1 §4.2, §4.3)
# ---------------------------------------------------------------------------

#: The selection scope's prompt version (part of its reuse key).
SELECTION_PROMPT_VERSION = READING_ACTIVE_PROMPT_VERSION
SELECTION_STYLES = ACTIVE_QUESTION_STYLES
#: The styles whose missed answer is a formative record and learner text
#: (spec §4.2 "Missed answers are learner text"); reconstruct is escalated.
FORMATIVE_STYLES = ("next_step", "why_step", "assumptions")
MISSED_SELF_CHECKS = ("partly", "no")
SELECTION_ACTIONS = ("answered", "self_checked", "dismissed")
SELECTION_CLAIM_TASK = "reader_selection_check"
#: How many of the book's following blocks fold while the learner tries the
#: next step, and the most selected blocks one question reads (display and
#: prompt-size bounds, never learning thresholds).
FOLD_BLOCKS = 3
MAX_SELECTED_BLOCKS = 12
MAX_SELECTION_CHARS = 10_000


def _clean(text: str | None) -> str:
    return " ".join((text or "").split())


def selection_claim_key(extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str) -> str:
    anchors = content_key([extraction_id, list(anchor_span_ids)])[:24]
    return f"{SELECTION_CLAIM_TASK}:{SELECTION_PROMPT_VERSION}:{style}:{anchors}"


def selection_view(
    repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str
) -> dict[str, Any]:
    """The bounded view of one selection (RW1b): the selected blocks in reading
    order inside the first one's guide section, one block of context before
    them and the book's next ``FOLD_BLOCKS`` blocks after them (the ones the
    Reader folds for the next step).

    ``{section_id, label, scope: "selection", style, anchor_span_ids,
    before, selected, following}``."""

    if style not in SELECTION_STYLES:
        raise ReaderQuickCheckError(f"unknown question style: {style!r}")
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderQuickCheckError(f"extraction has no IR: {extraction_id!r}")
    section_rows, block_by_span, span_to_section = extraction_sections(ir)
    wanted = [span_id for span_id in dict.fromkeys(anchor_span_ids) if span_id in span_to_section]
    if not wanted:
        raise ReaderQuickCheckError(f"the selection has no readable passage: {list(anchor_span_ids)!r}")
    section_id = span_to_section[wanted[0]]
    section = next(row for row in section_rows if row["id"] == section_id)
    order = list(section["span_ids"])
    anchors = sorted((span_id for span_id in wanted if span_id in order), key=order.index)[:MAX_SELECTED_BLOCKS]

    def block(span_id: str) -> dict[str, str] | None:
        found = block_by_span[span_id]
        text = _clean(found.text)
        return {"span_id": span_id, "kind": str(found.block_type or ""), "text": text} if text else None

    selected = [b for b in (block(span_id) for span_id in anchors) if b is not None]
    if not selected:
        raise ReaderQuickCheckError("the selection has no readable text")
    total = 0
    trimmed = []
    for item in selected:
        total += len(item["text"])
        if trimmed and total > MAX_SELECTION_CHARS:
            break
        trimmed.append(item)
    first, last = order.index(anchors[0]), order.index(anchors[-1])
    before = [b for b in (block(span_id) for span_id in order[max(0, first - 1):first]) if b is not None]
    following: list[dict[str, str]] = []
    for span_id in order[last + 1:]:
        item = block(span_id)
        if item is not None:
            following.append(item)
        if len(following) >= FOLD_BLOCKS:
            break
    return {
        "section_id": section_id,
        "label": section["label"],
        "scope": "selection",
        "style": style,
        "anchor_span_ids": [b["span_id"] for b in trimmed],
        "before": before,
        "selected": trimmed,
        "following": following if style == "next_step" else [],
    }


def folded_span_ids(repository: Repository, *, extraction_id: str, anchor_span_ids: list[str]) -> list[str]:
    """The book's next blocks after a selection, the ones that fold (G4's fold)."""

    try:
        view = selection_view(repository, extraction_id=extraction_id, anchor_span_ids=anchor_span_ids,
                              style="next_step")
    except ReaderQuickCheckError:
        return []
    return [b["span_id"] for b in view["following"]]


def request_active_question(client: StructuredTransport, context: ReadingActiveContext) -> ReadingActiveCheck:
    """Author one selection-scoped question (RW1b) as an isolated turn (the
    passage is untrusted source text, as for RW1a's passage check)."""

    return execute_structured_operation(
        client,
        purpose=PASSAGE_CHECK_PURPOSE,
        prompt=reading_active_prompt(context),
        result_model=ReadingActiveCheck,
        isolated=True,
    )


def _expected_answer(view: dict[str, Any], result: ReadingActiveCheck) -> tuple[str, str, list[str]]:
    """``(expected answer, answer basis, cited spans)``.

    The book's words are the expected answer only when they are the book's,
    by code: the next step is the book's following block(s) verbatim; a
    reconstruction is the selected derivation verbatim; a why-step or
    assumption answer is the book's only when the model's ``source_quote`` is
    found in the passage, otherwise it is the model's, labelled so (W2)."""

    style = view["style"]
    if style == "next_step":
        following = view["following"]
        if not following:
            raise ReaderQuickCheckError("nothing follows this line in its section, so there is no next step to try")
        named = [str(span_id) for span_id in result.next_step_span_ids]
        taken = []
        for item in following:
            if item["span_id"] not in named:
                break
            taken.append(item)
        taken = taken or following[:1]
        return "\n\n".join(item["text"] for item in taken), "source", [item["span_id"] for item in taken]
    if style == "reconstruct":
        selected = view["selected"]
        return "\n\n".join(item["text"] for item in selected), "source", [item["span_id"] for item in selected]
    blocks = [*view["before"], *view["selected"]]
    quote = _clean(result.source_quote)
    if quote:
        holding = [item["span_id"] for item in blocks if quote.lower() in item["text"].lower()]
        if holding:
            return quote, "source", holding
    expected = (result.expected_answer_md or "").strip()
    if not expected:
        raise ReaderQuickCheckError("the model returned no expected answer")
    valid = {item["span_id"] for item in blocks}
    cited = [span_id for span_id in result.span_ids if span_id in valid]
    return expected, "model", cited or list(view["anchor_span_ids"])


def selection_question(
    repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str
) -> dict[str, Any] | None:
    """The selection's question in ``style`` under its reuse key, any status."""

    return repository.selection_reader_authored_question(
        extraction_id=extraction_id, anchor_span_ids=list(anchor_span_ids), question_style=style,
        prompt_version=SELECTION_PROMPT_VERSION,
    )


def author_selection_question(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    anchor_span_ids: list[str] | tuple[str, ...],
    style: str,
    clock: Clock | None = None,
    spend: PassageCheckSpend | None = None,
    owner: str | None = None,
    owner_ended: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Author + persist one active-reading question on a selection (RW1b).

    One question per (extraction, anchor spans, style, prompt version), which
    the database keeps unique (migration 208): an existing row is reused, a
    dismissed one included, and the key is claimed durably before the model
    call, exactly as RW1a's inquiry check is. The call is admitted under the
    quick-check producer's caps (``[reader_inquiry]``) and sent as an isolated
    turn. Formative only (W1 tier 2): answering it writes no attempt."""

    if style not in SELECTION_STYLES:
        raise ReaderQuickCheckError(f"unknown question style: {style!r}")
    view = selection_view(repository, extraction_id=extraction_id, anchor_span_ids=anchor_span_ids, style=style)
    anchors = list(view["anchor_span_ids"])
    existing = selection_question(repository, extraction_id=extraction_id, anchor_span_ids=anchors, style=style)
    if existing is not None:
        return existing
    if style == "next_step" and not view["following"]:
        raise ReaderQuickCheckError("nothing follows this line in its section, so there is no next step to try")
    owner = owner or f"inline_{new_ulid()}"
    spend = spend if spend is not None else PassageCheckSpend()
    key = selection_claim_key(extraction_id, anchors, style)

    def claim(*, rerun: bool = False) -> tuple[str, int | None]:
        now = utc_now_iso(clock)
        with repository.atomic():
            connection = repository.connection()
            state, epoch = claim_work(
                connection, claim_key=key, task=SELECTION_CLAIM_TASK, producer=INQUIRY_CLAIM_PRODUCER,
                prompt_version=SELECTION_PROMPT_VERSION, input_hash=content_key([extraction_id, anchors, style]),
                owner=owner, now=now, lease_seconds=INQUIRY_CLAIM_LEASE_SECONDS, rerun=rerun,
            )
            if state == HELD and owner_ended is not None:
                holder = lease_holder(connection, claim_key=key)
                if holder is not None and owner_ended(holder):
                    epoch = take_over_claim(connection, claim_key=key, from_owner=holder, owner=owner, now=now,
                                            lease_seconds=INQUIRY_CLAIM_LEASE_SECONDS)
                    state = CLAIMED if epoch is not None else HELD
            return state, epoch

    state, epoch = claim()
    if state == DONE:
        landed = selection_question(repository, extraction_id=extraction_id, anchor_span_ids=anchors, style=style)
        if landed is not None:
            return landed
        state, epoch = claim(rerun=True)
    if state == HELD or epoch is None:
        raise InquiryCheckHeld("Another worker is writing this question.")
    try:
        result = _admitted_passage_check(
            repository, client, ReadingActiveContext(extraction_id=extraction_id, style=style, passage=view),
            spend=spend, owner_id=key, clock=clock, prompt=reading_active_prompt, request=request_active_question,
        )
        question_md = (result.question_md or "").strip()
        if not question_md:
            raise ReaderQuickCheckError("the model returned an empty question")
        expected, basis, span_ids = _expected_answer(view, result)
    except BaseException:
        with repository.atomic():
            release_claim(repository.connection(), claim_key=key, owner=owner, epoch=epoch, now=utc_now_iso(clock))
        raise
    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    question_id: str | None = None
    with repository.atomic():
        connection = repository.connection()
        if holds_claim(connection, claim_key=key, owner=owner, epoch=epoch):
            question_id = repository.insert_reader_authored_question(
                fields={
                    "extraction_id": extraction_id,
                    "section_id": view["section_id"],
                    "source_id": revision.get("source_id"),
                    "question_md": question_md,
                    "expected_answer_md": expected,
                    "span_ids": span_ids,
                    "prompt_version": SELECTION_PROMPT_VERSION,
                    "provider": getattr(getattr(client, "config", None), "provider", None)
                    or getattr(client, "provider_name", None),
                    "model": getattr(getattr(client, "config", None), "model", None) or getattr(client, "model", None),
                    "scope_kind": "selection",
                    "question_style": style,
                    "anchor_span_ids": anchors,
                    "answer_basis": basis,
                },
                clock=clock,
            )
            complete_claim(connection, claim_key=key, owner=owner, epoch=epoch, judgment_id=question_id,
                           now=utc_now_iso(clock))
    if question_id is None:
        landed = selection_question(repository, extraction_id=extraction_id, anchor_span_ids=anchors, style=style)
        if landed is not None:
            return landed
        raise InquiryCheckHeld("Another worker took this question over.")
    row = repository.get_reader_authored_question(question_id)
    assert row is not None
    return row


def is_missed(row: dict[str, Any]) -> bool:
    """A missed formative answer: partly or no on a next step, why step or assumption."""

    return (row.get("scope_kind") == "selection" and row.get("question_style") in FORMATIVE_STYLES
            and row.get("self_check") in MISSED_SELF_CHECKS)


def record_selection_action(
    repository: Repository,
    *,
    question_id: str,
    action: str,
    response_md: str | None = None,
    self_check: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The learner's act on an active-reading question (RW1b).

    ``answered`` stamps their answer (or none: "show me" reveals the book's
    lines without one), after which the expected answer is shown beside it;
    ``self_checked`` records matches, partly or no in ``self_check`` and, in
    the same transaction, a ``learner_card`` verdict on ``judgment_ledger``
    (a changed verdict supersedes the previous one); ``dismissed`` is the
    durable "don't bring this back". Formative only: no attempt, observation,
    mastery or FSRS row. Whether a missed answer becomes learner text is the
    caller's (``reader_formative``)."""

    if action not in SELECTION_ACTIONS:
        raise ReaderQuickCheckError(f"unknown question action: {action!r}")
    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row.get("scope_kind") != "selection":
        raise ReaderQuickCheckError("not an active-reading question")
    if row["status"] == "escalated":
        raise ReaderQuickCheckError("this question was already added to practice")
    if action == "self_checked":
        if self_check not in SELF_CHECKS:
            raise ReaderQuickCheckError(f"unknown self-check: {self_check!r}")
        if row["status"] != "answered":
            raise ReaderQuickCheckError("answer the question, or show the book's lines, before comparing")
        with repository.atomic():
            repository.transition_reader_authored_question(
                question_id=question_id, status="answered", self_check=self_check, clock=clock
            )
            _append_self_check_verdict(repository, row, self_check, clock=clock)
    elif action == "answered":
        if row["status"] == "answered":
            raise ReaderQuickCheckError("this question was already answered")
        repository.transition_reader_authored_question(
            question_id=question_id, status="answered", response_md=(response_md or "").strip() or None, clock=clock
        )
    else:
        repository.transition_reader_authored_question(question_id=question_id, status="dismissed", clock=clock)
    refreshed = repository.get_reader_authored_question(question_id)
    assert refreshed is not None
    return refreshed
