"""Paid preparation and cache loading for the ``llm_probability`` V1-V3 arms.

Preparation is the only step that calls a model, and it runs only when the
owner asks for it (``learnloop eval --section field --probability-arm ...
--llm-cache DIR --prepare-llm``). It:

1. walks the replay rows in the harness's own order, collecting each
   prediction's past exactly as the harness will hand it to the arms, plus
   the incumbent's numbers from that same past;
2. renders every variant's ``state`` from one read-only snapshot
   (``probability_states``) and closes it before any request;
3. admits the whole remaining plan under the Phase 1 spend caps (a dry run
   stops here), then sends one request per uncached state, reserving each
   physical attempt, recording a receipt labelled with the judge, the
   question-set version and the state hash, and appending every returned
   verdict to ``judgment_ledger``;
4. checkpoints each probability outside the vault, so the replay (and any
   rebuild) makes zero calls.

Each judge has its own budget because billing differs: the Decider is
metered at its listed input price (output is free); the LLM route is metered
(an owner-supplied price, one physical request per call) or Codex on the
owner's subscription (estimated cost only, Slice A plan §5 rule 6).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import time
from typing import Any

from learnloop.ai.decisions import DecisionResponseInvalid, NoulQuestion, request_body
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import (
    call_labels, generation_limit, observe_model_calls, single_request,
)
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import (
    ESTIMATED_ONLY, SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded,
    subscription_usage_estimate,
)
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.clock import parse_utc
from learnloop.db.stores.judgments import append_judgment
from learnloop.field.evaluation import _eligible, _groups
from learnloop.field.predictors import create_predictor
from learnloop.field.probability_arms import (
    CachedProbabilityArm, JUDGES, VARIANTS, clip, position_key,
)
from learnloop.field.probability_states import (
    PredictionPoint, STATE_VERSION, StateRenderer, canonical_json, history_pairs, start_index, state_hash,
)
from learnloop.field.types import AttemptRow, SignalRow

TASK = "llm_probability"
QUESTION_NAME = "will_pass"
QUESTION_TEXT = "Will the learner answer this item correctly on this attempt?"
#: The Decider's versioned question set (router spec §6.3 style).
QUESTION_SET_VERSION = "llm_probability_qs_v1"
#: The LLM judge's structured-output prompt.
LLM_PROMPT_VERSION = "llm_probability_llm_v1"
DECIDER_QUESTIONS = {
    QUESTION_NAME: NoulQuestion(
        instructions=(
            f"{QUESTION_TEXT} Judge only from the state: the item and, where given, "
            "the learner's earlier work, which all happened before this attempt began."
        ),
        when_true="The learner's answer to this item will be fully or almost fully correct.",
        when_false="The answer will be wrong or incomplete, or the learner will not know.",
    ),
}
LLM_INSTRUCTIONS = (
    f"{QUESTION_TEXT} Judge only from the state: the item and, where given, the learner's "
    "earlier work, which all happened before this attempt began. Return p_correct, your "
    "probability strictly between 0 and 1 that the answer will be fully or almost fully correct."
)
#: Output allowance for the Decider's typed answer (output tokens are free).
DECIDER_OUTPUT_TOKENS = 16
#: Waits honoured for a 429 Retry-After before a counted retry.
MAX_RETRY_AFTER_SECONDS = 10.0


class ProbabilityJudgment(WireModel):
    # Range validation happens after the paid verdict is ledgered.
    p_correct: float


def _digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


# -- the harness's past ---------------------------------------------------


def _observes(row: Any) -> bool:
    """What the incumbent folds: every signal and every scored attempt."""

    return isinstance(row, SignalRow) or _eligible(row)


def _incumbent_numbers(ekf: Any, row: AttemptRow, observations: int) -> dict[str, Any]:
    prediction = ekf.predict_item(row.features)
    spread = 1.959963984540054 * math.sqrt(max(0.0, prediction.logit_variance))
    logit = math.log(prediction.p_success / (1 - prediction.p_success))
    return {
        "name": "mastery_ekf",
        "p_success": round(prediction.p_success, 4),
        "p_success_interval95": [
            round(1 / (1 + math.exp(-(logit - spread))), 4),
            round(1 / (1 + math.exp(-(logit + spread))), 4),
        ],
        "observations_before_start": observations,
        "regions": {
            lo: {"mean": region.mean, "variance": region.variance, "n_eff": region.n_eff,
                 "untested": region.untested}
            for lo, region in ekf.region_estimates().items()
        },
    }


def prediction_points(
    rows: Iterable[Any], *, incumbent: Mapping[str, Any] | None = None,
    start_of: Callable[[str], datetime | None] | None = None,
) -> list[PredictionPoint]:
    """Every prediction the harness will ask an attempt arm for, in order.

    Mirrors ``evaluate``: signals and attempts in ``_groups`` order; an
    attempt arm predicts and then observes exactly the rows the harness
    scores for ability (``_eligible``). ``history`` is that harness past (it
    keys the cache).

    The incumbent's numbers (``mastery_ekf``) are fitted only on the
    observations made strictly before the attempt's start, ``start_of(id)``
    (the renderer's cutoff), never on the harness past: an attempt that
    completed after this one began must not move them (review F2). An
    unknown start folds nothing, so the numbers are the frozen priors alone.
    """

    events = [row for row, _facets in _groups(tuple(rows))]
    times = [parse_utc(row.observed_at) for row in events]
    history: list[AttemptRow] = []
    staged: list[tuple[int, int, AttemptRow, tuple[AttemptRow, ...], str]] = []
    for index, row in enumerate(events):
        if isinstance(row, SignalRow) or not _eligible(row):
            continue
        cutoff = start_of(row.attempt_id) if start_of is not None else None
        prefix = min(start_index(times, cutoff), index)
        staged.append((prefix, len(staged), row, tuple(history),
                       position_key(row.features, history_pairs(history))))
        history.append(row)
    # One incumbent walks the time-ordered stream once; each prediction reads
    # it at its own prefix (shorter prefixes first).
    ekf = create_predictor("mastery_ekf", **dict(incumbent or {}))
    folded = observations = 0
    numbers: dict[int, dict[str, Any]] = {}
    for prefix, order, row, _past, _key in sorted(staged, key=lambda entry: (entry[0], entry[1])):
        while folded < prefix:
            if _observes(events[folded]):
                ekf.observe(events[folded])
                observations += 1
            folded += 1
        numbers[order] = _incumbent_numbers(ekf, row, observations)
    return [
        PredictionPoint(position_key=key, row=row, history=past, incumbent=numbers[order])
        for _prefix, order, row, past, key in staged
    ]


@dataclass(frozen=True)
class RenderedRequest:
    variant: str
    request_digest: str
    state: Any
    state_hash: str


@dataclass
class RenderedPlan:
    """Per variant: every position's request digest, and each distinct state."""

    positions: dict[str, dict[str, str]] = field(default_factory=dict)
    requests: dict[str, RenderedRequest] = field(default_factory=dict)

    def for_variant(self, variant: str) -> list[RenderedRequest]:
        digests = dict.fromkeys(self.positions.get(variant, {}).values())
        return [self.requests[digest] for digest in digests]


def render_plan(points: Sequence[PredictionPoint], variants: Iterable[str], renderer: StateRenderer) -> RenderedPlan:
    plan = RenderedPlan()
    for variant in variants:
        if variant not in VARIANTS:
            raise ValueError(f"Unknown variant {variant!r}")
        positions = plan.positions.setdefault(variant, {})
        for point in points:
            state = renderer.render(variant, point)
            hashed = state_hash(state)
            digest = _digest({"state_version": STATE_VERSION, "variant": variant, "state_hash": hashed})
            positions[point.position_key] = digest
            plan.requests.setdefault(digest, RenderedRequest(variant, digest, state, hashed))
    return plan


# -- judges --------------------------------------------------------------


@dataclass
class JudgeRoute:
    """A resolved judge route; ``settings`` is non-secret and hashed into the cache."""

    judge: str
    provider: str
    model: str
    settings: Mapping[str, Any]
    subscription: bool = False
    price_per_million: float | None = None
    output_tokens: int = DECIDER_OUTPUT_TOKENS
    client_factory: Callable[[], Any] | None = None

    @property
    def version(self) -> str:
        return QUESTION_SET_VERSION if self.judge == "decider" else LLM_PROMPT_VERSION

    @property
    def settings_hash(self) -> str:
        return _digest(dict(self.settings))


def llm_prompt(state: Any) -> str:
    return render_structured_prompt("Predict the learner's next answer", LLM_PROMPT_VERSION, {
        "instructions": LLM_INSTRUCTIONS, "state": state,
    })


def request_estimate(route: JudgeRoute, request: RenderedRequest) -> SpendEstimate:
    """A conservative per-request estimate, before any call."""

    if route.judge == "decider":
        body = request_body(route.model, request.state, DECIDER_QUESTIONS)
        tokens = math.ceil(len(json.dumps(body, ensure_ascii=False).encode("utf-8")) / 3)
        price = route.price_per_million
        return SpendEstimate(
            candidates=1, calls=1, total_tokens=tokens + route.output_tokens,
            estimated_usd=None if price is None else tokens * price / 1_000_000,
        )
    # UTF-8 bytes bound byte-level tokens; plus schema, envelope and output.
    tokens = (len(llm_prompt(request.state).encode("utf-8"))
              + len(repr(ProbabilityJudgment.model_json_schema()).encode()) + 2048 + route.output_tokens)
    return SpendEstimate(
        candidates=1, calls=1, total_tokens=tokens,
        estimated_usd=None if route.price_per_million is None else tokens * route.price_per_million / 1_000_000,
    )


def _sum(estimates: Iterable[SpendEstimate]) -> SpendEstimate:
    estimates = list(estimates)
    usd = [e.estimated_usd for e in estimates]
    return SpendEstimate(
        candidates=sum(e.candidates for e in estimates), calls=sum(e.calls for e in estimates),
        total_tokens=sum(e.total_tokens for e in estimates),
        estimated_usd=(sum(usd) if all(u is not None for u in usd) else None) if estimates else 0.0,
    )


# -- cache ---------------------------------------------------------------


def _cache_path(directory: Path, route: JudgeRoute, digest: str) -> Path:
    name = _digest([route.model, route.settings_hash, route.version, digest])
    return directory / TASK / route.judge / f"{name}.json"


def _read_cached(directory: Path, route: JudgeRoute, request: RenderedRequest) -> dict[str, Any] | None:
    path = _cache_path(directory, route, request.request_digest)
    if not path.is_file():
        return None
    cached = json.loads(path.read_text(encoding="utf-8"))
    p = cached.get("p")
    if (cached.get("judge") != route.judge or cached.get("model") != route.model
            or cached.get("settings_hash") != route.settings_hash or cached.get("version") != route.version
            or cached.get("request_digest") != request.request_digest
            or cached.get("state_hash") != request.state_hash or not cached.get("judgment_id")
            or isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 1):
        raise ValueError("Invalid llm_probability checkpoint; remove it to prepare again")
    return cached


def _write_checkpoint(path: Path, checkpoint: Mapping[str, Any]) -> None:
    """One completed prediction per file; an interruption never corrupts a finished entry."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(dict(checkpoint), sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _valid_probability(value: Any) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and 0 <= value <= 1)


def _identity(judge: str, version: str, settings_hash: str, request_digest: str, state_hash_: str,
              state_version: str = STATE_VERSION) -> tuple[str, ...]:
    return (judge, version, settings_hash, request_digest, state_hash_, state_version)


def committed_judgments(connection: Any) -> dict[tuple[str, ...], dict[str, Any]]:
    """Valid verdicts already committed to ``judgment_ledger``, by request identity.

    A paid answer is durable once its judgment commits, even if the run
    stopped before the cache file was renamed into place. The ledger row
    carries the whole identity (judge, question-set version, route settings
    hash, request digest, state hash, state version), so resuming recovers
    the checkpoint from it instead of paying again (review F4). The earliest
    valid verdict wins; invalid ones (no score) are never recovered.
    """

    found: dict[tuple[str, ...], dict[str, Any]] = {}
    for identifier, left_id, judge, judge_model, version, input_hash, score, rationale in connection.execute(
        "SELECT id, left_id, judge, judge_model, prompt_version, input_hash, score, rationale "
        "FROM judgment_ledger WHERE task=? AND left_kind='probability_request' ORDER BY created_at, id",
        (TASK,),
    ):
        if not _valid_probability(score):
            continue
        try:
            context = json.loads(rationale or "{}")
        except ValueError:
            continue
        if not isinstance(context, dict) or not context.get("settings_hash"):
            continue
        key = _identity(str(judge), str(version or ""), str(context["settings_hash"]), str(left_id),
                        str(input_hash), str(context.get("state_version") or ""))
        found.setdefault(key, {
            "judgment_id": str(identifier), "p": float(score), "resolved_model": judge_model,
            "requested_model": context.get("requested_model"),
        })
    return found


def check_cache_location(cache_dir: Path, vault_root: Path) -> Path:
    directory, vault = Path(cache_dir).resolve(), Path(vault_root).resolve()
    if directory == vault or vault in directory.parents:
        raise ValueError("The llm_probability cache must be outside the vault")
    return directory


def load_arms(
    plan: RenderedPlan, *, cache_dir: Path, routes: Mapping[str, JudgeRoute],
    selection: Sequence[tuple[str, str]],
) -> tuple[list[CachedProbabilityArm], dict[str, Any]]:
    """Cache-only: no client, no repository, no call. Missing entries fail closed."""

    arms: list[CachedProbabilityArm] = []
    report: dict[str, Any] = {"arms": {}, "missing": {}}
    for variant, judge in selection:
        route = routes[judge]
        probabilities, models, missing = {}, set(), 0
        cached_by_digest: dict[str, dict[str, Any] | None] = {}
        for key, digest in plan.positions.get(variant, {}).items():
            if digest not in cached_by_digest:
                cached_by_digest[digest] = _read_cached(cache_dir, route, plan.requests[digest])
            cached = cached_by_digest[digest]
            if cached is None:
                missing += 1
                continue
            probabilities[key] = float(cached["p"])
            models.add(cached.get("resolved_model") or route.model)
        label = f"{variant}/{judge}"
        if missing:
            report["missing"][label] = missing
            continue
        provenance = {
            "judge": judge, "variant": variant, "version": route.version, "state_version": STATE_VERSION,
            "settings_hash": route.settings_hash, "requested_model": route.model,
        }
        model = "+".join(sorted(models)) or route.model
        for recalibrated in (False, True):
            arms.append(CachedProbabilityArm(
                variant=variant, judge=judge, probabilities=probabilities, model=model,
                provenance=provenance, recalibrated=recalibrated,
            ))
        report["arms"][label] = {
            "predictions": len(probabilities), "distinct_requests": len(cached_by_digest),
            "model": model, "requested_model": route.model, "version": route.version,
        }
    return arms, report


# -- paid preparation ------------------------------------------------------


@dataclass
class _Attempt:
    usage: dict[str, Any] = field(default_factory=dict)
    physical_calls: int = 0


def _call_decider(client: Any, request: RenderedRequest) -> tuple[float | None, dict[str, Any]]:
    result = client.decide(request.state, DECIDER_QUESTIONS, purpose=TASK)
    answer = result.answers[QUESTION_NAME]
    verdict = {"noul": answer.p_yes, "model": result.model, "id": result.response_id,
               "provider": result.provider}
    return answer.p_yes, verdict


def _call_llm(client: Any, route: JudgeRoute, request: RenderedRequest) -> tuple[float | None, dict[str, Any]]:
    # Codex turns cannot bound physical requests; metered routes must
    # (one request, no hidden repair or retry). Every turn is isolated: the
    # model sees the prompt only, never the vault or its files.
    bound = nullcontext() if route.subscription else single_request()
    with bound, generation_limit(route.output_tokens):
        result = execute_structured_operation(
            client, purpose=TASK, prompt=llm_prompt(request.state),
            result_model=ProbabilityJudgment, isolated=True,
        )
    verdict = result.model_dump(mode="json")
    value = verdict.get("p_correct")
    # 0 and 1 are valid (overconfident) answers; the arm clips them, as it
    # clips the Decider's. Anything else is ledgered as invalid, not cached.
    return (float(value) if _valid_probability(value) else None), verdict


def prepare_judge(
    plan: RenderedPlan, *, route: JudgeRoute, variants: Sequence[str], cache_dir: Path,
    repository: Any, caps: SpendCaps, dry_run: bool = False,
    cancelled: Callable[[], bool] | None = None, sleep: Callable[[float], None] = time.sleep,
    committed: Mapping[tuple[str, ...], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Prepare one judge's uncached requests; returns an aggregate-only report.

    ``committed`` is :func:`committed_judgments` read from the caller's
    snapshot (read from ``repository`` when omitted). A request whose verdict
    already committed is recovered into the cache with no call; a dry run
    only counts it.
    """

    requests: dict[str, RenderedRequest] = {}
    for variant in variants:
        for request in plan.for_variant(variant):
            requests.setdefault(request.request_digest, request)
    if committed is None:
        committed = {}
        if repository is not None:
            with repository.connection() as connection:
                committed = committed_judgments(connection)
    directory = Path(cache_dir)
    uncached = [r for r in requests.values() if _read_cached(cache_dir, route, r) is None]
    recoverable: list[tuple[RenderedRequest, Mapping[str, Any]]] = []
    pending: list[RenderedRequest] = []
    for request in uncached:
        verdict = committed.get(_identity(route.judge, route.version, route.settings_hash,
                                          request.request_digest, request.state_hash))
        if verdict is not None and verdict.get("requested_model") in (None, route.model):
            recoverable.append((request, verdict))
        else:
            pending.append(request)
    if not dry_run:
        for request, verdict in recoverable:
            _write_checkpoint(_cache_path(directory, route, request.request_digest), {
                "judge": route.judge, "model": route.model,
                "resolved_model": verdict.get("resolved_model") or route.model,
                "settings_hash": route.settings_hash, "version": route.version,
                "state_version": STATE_VERSION, "variant": request.variant,
                "request_digest": request.request_digest, "state_hash": request.state_hash,
                "p": float(verdict["p"]), "judgment_id": verdict["judgment_id"],
                "usage": {"input_tokens": None, "output_tokens": None, "cost": None},
                "recovered_from": "judgment_ledger",
            })
    per_request = {r.request_digest: request_estimate(route, r) for r in pending}
    estimate = _sum(per_request.values())
    budget = SpendBudget(caps, cancelled=cancelled, subscription=route.subscription)
    report: dict[str, Any] = {
        "judge": route.judge, "provider": route.provider, "model": route.model,
        "version": route.version, "state_version": STATE_VERSION,
        "settings_hash": route.settings_hash, "requests": len(requests),
        "cached": len(requests) - len(uncached), "pending": len(pending),
        ("recoverable" if dry_run else "recovered"): len(recoverable),
        "completed": 0, "invalid": 0, "retries": 0,
        "estimate": asdict(estimate),
        "price_per_million": route.price_per_million,
        "price_source": ("listed_input_price" if route.judge == "decider"
                         else "owner_override" if route.price_per_million is not None else "unknown"),
        "billing": "subscription" if route.subscription else "metered",
        "cost_basis": ESTIMATED_ONLY if route.subscription else "metered_caps",
        "physical_request_bound": not route.subscription,
        "caps_in_force": budget.declared(),
        "charged": asdict(budget.used), "resolved_models": {},
        "status": "dry_run" if dry_run else "pending",
    }
    try:
        budget.check(estimate)
    except AIInterrupted:
        report["status"] = "cancelled"
        return report
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    if dry_run or not pending:
        if not dry_run:
            report["status"] = "complete"
        return report
    try:
        client = route.client_factory() if route.client_factory is not None else None
    except AIProviderUnavailable as exc:
        report.update(status="unavailable", error_type=type(exc).__name__, reason=str(exc)[:300])
        return report
    if client is None:
        report.update(status="unavailable", reason=f"The {route.judge} judge route is unavailable")
        return report
    current = _Attempt()
    current_digest = ""

    def observe(action: str, event: dict[str, Any]) -> None:
        if action == "start" and not route.subscription and (
            event.get("purpose") == "chat_request" or str(event.get("purpose", "")).endswith(":sdk_turn")
        ):
            if current.physical_calls:
                raise SpendLimitExceeded("Hidden physical retries are prohibited on a metered route")
            current.physical_calls += 1
        if action != "start":
            for name in ("input_tokens", "output_tokens", "cost", "resolved_model"):
                if event.get(name) is not None:
                    current.usage[name] = (event[name] if name == "resolved_model"
                                           else max(current.usage.get(name, 0), event[name]))
            if route.subscription:
                event = {**event, "usage_json": json.dumps({
                    **json.loads(event.get("usage_json") or "{}"),
                    **subscription_usage_estimate(
                        event, planned_tokens=per_request[current_digest].total_tokens,
                        price_per_token=(route.price_per_million / 1_000_000
                                         if route.price_per_million is not None else None),
                    ),
                }, sort_keys=True)}
        repository.record_model_event(action, event, owner_kind=TASK, owner_id=current_digest)

    try:
        for request in pending:
            current_digest = request.request_digest
            attempt = 0
            while True:
                current.usage.clear()
                current.physical_calls = 0
                planned = per_request[request.request_digest]
                reservation = replace(planned, candidates=int(attempt == 0), retries=int(attempt > 0))
                try:
                    with budget.request(reservation) as charge, observe_model_calls(observe), call_labels(
                        judge=route.judge, question_set_version=route.version, state_hash=request.state_hash,
                    ):
                        try:
                            if route.judge == "decider":
                                p, verdict = _call_decider(client, request)
                            else:
                                p, verdict = _call_llm(client, route, request)
                        finally:
                            tokens = int(current.usage.get("input_tokens", 0) or 0) + int(
                                current.usage.get("output_tokens", 0) or 0)
                            cost = current.usage.get("cost")
                            if route.judge == "decider" and cost is None and current.usage.get("input_tokens"):
                                cost = current.usage["input_tokens"] * (route.price_per_million or 0.0) / 1_000_000
                            if route.judge == "llm" and route.price_per_million is not None and tokens:
                                cost = max(cost or 0.0, tokens * route.price_per_million / 1_000_000)
                            if route.subscription and route.price_per_million is None:
                                cost = None  # estimated tokens only; never refused
                            charge.reconcile(total_tokens=tokens or None, estimated_usd=cost)
                except AIInterrupted:
                    raise
                except SpendLimitExceeded:
                    raise
                except DecisionResponseInvalid:
                    # A paid 200 in an undocumented shape: the API moved.
                    # Fail closed rather than pay again for the same answer.
                    raise
                except AIProviderUnavailable as exc:
                    retry_after = getattr(exc, "retry_after", None)
                    status = getattr(exc, "status", None)
                    retryable = status in (None, 429) or (isinstance(status, int) and status >= 500)
                    if not retryable or budget.used.retries >= caps.max_retries:
                        raise
                    if status == 429 and retry_after is not None and retry_after <= MAX_RETRY_AFTER_SECONDS:
                        sleep(retry_after)
                    attempt += 1
                    report["retries"] += 1
                    continue
                break
            model = current.usage.get("resolved_model") or route.model
            report["resolved_models"][model] = report["resolved_models"].get(model, 0) + 1
            with repository.connection() as connection:
                judgment_id = append_judgment(
                    connection, task=TASK, left_kind="probability_request", left_id=request.request_digest,
                    judge=route.judge, judge_model=model, prompt_version=route.version,
                    input_hash=request.state_hash, verdict=json.dumps(verdict, sort_keys=True),
                    score=p, rationale=json.dumps({
                        "variant": request.variant, "state_version": STATE_VERSION,
                        "settings_hash": route.settings_hash, "requested_model": route.model,
                        "question": QUESTION_TEXT,
                    }, sort_keys=True),
                )
            if p is None:
                report["invalid"] += 1
                continue
            checkpoint = {
                "judge": route.judge, "model": route.model, "resolved_model": model,
                "settings_hash": route.settings_hash, "version": route.version,
                "state_version": STATE_VERSION, "variant": request.variant,
                "request_digest": request.request_digest, "state_hash": request.state_hash,
                "p": p, "judgment_id": judgment_id,
                "usage": {key: current.usage.get(key) for key in ("input_tokens", "output_tokens", "cost")},
            }
            # The verdict is already durable in the ledger: an interruption
            # here is recovered from it on resume, never paid for again.
            _write_checkpoint(_cache_path(directory, route, request.request_digest), checkpoint)
            report["completed"] += 1
        report["status"] = "complete" if not report["invalid"] else "incomplete"
    except (AIInterrupted, KeyboardInterrupt):
        report["status"] = "cancelled"
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
    except AIProviderUnavailable as exc:
        report.update(status="provider_failed", error_type=type(exc).__name__,
                      reason=str(exc)[:300])
    finally:
        report["charged"] = asdict(budget.used)
    return report


__all__ = [
    "DECIDER_QUESTIONS",
    "JudgeRoute",
    "LLM_PROMPT_VERSION",
    "ProbabilityJudgment",
    "QUESTION_NAME",
    "QUESTION_SET_VERSION",
    "QUESTION_TEXT",
    "RenderedPlan",
    "RenderedRequest",
    "TASK",
    "check_cache_location",
    "committed_judgments",
    "llm_prompt",
    "load_arms",
    "prediction_points",
    "prepare_judge",
    "render_plan",
    "request_estimate",
]
