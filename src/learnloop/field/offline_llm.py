"""Opt-in offline sensor preparation; replay itself has no model/store access.

Preparation reserves Phase-1 spend before each request, writes verdicts to the
append-only judgment ledger and records model-call receipts. Raw probabilities
are cached outside the vault. The returned point-only arm owns only numbers.

A Codex route is billed to the owner's subscription (Slice A §5 rule 6): no
physical-request bound, token and dollar caps not enforced, unknown price
admitted; the candidate and call caps still apply. Receipts record the token
estimate as ``estimated_only``. Metered routes keep the full cap set and the
one-physical-request bound.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import json
from math import exp, isfinite, log
from pathlib import Path
from types import SimpleNamespace

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import model_call, observe_model_calls
from learnloop.ai.spend import (
    ESTIMATED_ONLY, SpendBudget, SpendEstimate, SpendLimitExceeded, subscription_usage_estimate,
)
from learnloop.db.stores.judgments import append_judgment
from learnloop.field.evaluation import _eligible, _groups, _hash
from learnloop.field.types import FacetRow, ItemFeatures, SignalRow


PROMPT_VERSION = "field-llm-probability-v1"
TASK = "field_llm_probability"
HISTORY_LIMIT = 20


def _request(features, history):
    return {"prompt_version": PROMPT_VERSION, "item": asdict(features),
            "past_attempts": history[-HISTORY_LIMIT:]}


def _past(row):
    return {"item": asdict(row.features), "outcome": row.outcome,
            "effective_mass": row.effective_mass, "hints_used": row.hints_used}


def _probability(raw):
    value = raw.get("p_success")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0 < value < 1:
        raise ValueError("LLM probability must be finite and strictly between zero and one")
    return float(value)


class CachedProbabilityArm:
    """No I/O. A one-parameter online logit-intercept recalibrator, past only."""

    name = "llm_probability"
    granularity = "attempt"
    calibrated_uncertainty = False

    def __init__(self, probabilities, *, model, settings=None):
        self._probabilities = dict(probabilities)
        self.model = model
        self.version_hash = _hash({"prompt": PROMPT_VERSION, "model": model,
                                   "settings": settings or {},
                                   "recalibration": "intercept-sgd-0.1-v1",
                                   "probabilities": probabilities})
        self._history = []
        self.intercept = 0.

    def predict(self, features):
        if not isinstance(features, ItemFeatures):
            raise TypeError("Prediction requires outcome-free ItemFeatures")
        key = _hash(_request(features, self._history))
        p = self._probabilities[key]
        return 1 / (1 + exp(-max(-20., min(20., log(p / (1 - p)) + self.intercept))))

    def observe(self, row):
        if isinstance(row, (SignalRow, FacetRow)) or not _eligible(row):
            return
        # Calculate from the still-past state. The just-revealed outcome changes
        # the next prediction, never the one already evaluated.
        p = self.predict(row.features)
        self.intercept = max(-5., min(5., self.intercept + .1 * (row.outcome - p)))
        self._history.append(_past(row))

    def rebuild(self, rows):
        self._history = []
        self.intercept = 0.
        for row, _ in _groups(rows):
            self.observe(row)


def prediction_requests(rows):
    """Frozen past-only inputs, also used to estimate spend before preparation."""
    history, requests = [], {}
    for row, _ in _groups(tuple(rows)):
        if isinstance(row, SignalRow) or not _eligible(row):
            continue
        request = _request(row.features, history)
        requests[_hash(request)] = request
        history.append(_past(row))
    return requests


def _read_cache(requests, directory, model, settings):
    probabilities, pending = {}, {}
    settings_hash = _hash(settings or {})
    for digest, request in requests.items():
        path = directory / f"{_hash([model, PROMPT_VERSION, settings_hash, digest])}.json"
        if path.is_file():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if (cached.get("model") != model or cached.get("input_hash") != digest
                    or cached.get("settings_hash") != settings_hash
                    or cached.get("prompt_version") != PROMPT_VERSION
                    or not cached.get("judgment_id")):
                raise ValueError("Invalid offline probability checkpoint")
            probabilities[digest] = _probability(cached)
        else:
            pending[digest] = (request, path)
    return probabilities, pending


def load_cached_probability_arm(rows, *, cache_dir, model, settings=None):
    """Load a complete offline arm without clients, receipts, credentials or calls.

    Missing checkpoints fail closed. ``settings`` is the non-secret effective
    model route (endpoint, effort and output limits included), as for preparation.
    """
    probabilities, pending = _read_cache(prediction_requests(rows), Path(cache_dir), model, settings)
    if pending:
        raise ValueError(f"Offline probability cache incomplete: {len(pending)} predictions missing")
    return CachedProbabilityArm(probabilities, model=model, settings=settings)


def prepare_llm_probability(
    rows, *, repository, cache_dir, vault_path, model, predict,
    estimate_per_prediction, caps, enabled=False, dry_run=False, cancelled=None,
    settings=None, subscription=False,
):
    """Return ``(pure_arm_or_None, aggregate_spend_report)``.

    The callback is lazy. On a metered route it must use a single-physical-call
    OpenAI transport; hidden retry starts are refused. ``subscription`` (a Codex
    route) lifts that bound and the token/dollar caps, estimating cost only. It
    receives numeric item features and only preceding graded attempts, not the
    current outcome. No credentials are read here. Disabled mode does not read
    cache or repository.
    """
    summary = {"status": "disabled", "model": model, "prompt_version": PROMPT_VERSION,
               "predictions": 0, "cached": 0, "invalid": 0, "caps": caps.as_dict()}
    if not enabled:
        return None, summary
    if not model.strip():
        raise ValueError("An explicit offline model is required")
    if estimate_per_prediction.calls != 1 or estimate_per_prediction.retries:
        raise ValueError("Declare exactly one physical call and no hidden retries")
    directory, vault = Path(cache_dir).resolve(), Path(vault_path).resolve()
    if directory == vault or vault in directory.parents:
        raise ValueError("Offline probability cache must be outside the vault")
    budget = SpendBudget(caps, cancelled=cancelled, subscription=subscription)
    requests = prediction_requests(rows)
    probabilities, pending = _read_cache(requests, directory, model, settings)
    count = len(pending)
    estimate = SpendEstimate(
        candidates=count, calls=count, total_tokens=count * estimate_per_prediction.total_tokens,
        estimated_usd=count * estimate_per_prediction.estimated_usd
        if estimate_per_prediction.estimated_usd is not None else (None if count else 0.),
    )
    summary.update(status="dry_run" if dry_run else "complete", predictions=len(requests),
                   cached=len(probabilities), settings_hash=_hash(settings or {}),
                   estimate=asdict(estimate), charged=asdict(budget.used),
                   billing="subscription" if subscription else "metered",
                   cost_basis=ESTIMATED_ONLY if subscription else "metered_caps",
                   physical_request_bound=not subscription,
                   caps_in_force=budget.declared())
    price_per_token = (
        estimate_per_prediction.estimated_usd / estimate_per_prediction.total_tokens
        if estimate_per_prediction.estimated_usd is not None and estimate_per_prediction.total_tokens
        else None
    )
    try:
        budget.check(estimate)
        if dry_run:
            return None, summary
        directory.mkdir(parents=True, exist_ok=True)
        for digest, (request, path) in pending.items():
            usage, physical_calls = {}, 0

            def observe(action, event):
                nonlocal physical_calls
                if action == "start" and not subscription and (
                    event.get("purpose") == "chat_request"
                    or str(event.get("purpose", "")).endswith(":sdk_turn")
                ):
                    if physical_calls:
                        raise SpendLimitExceeded("Hidden offline probability retries are prohibited")
                    physical_calls += 1
                if action != "start" and subscription:
                    event = {**event, "usage_json": json.dumps({
                        **json.loads(event.get("usage_json") or "{}"),
                        **subscription_usage_estimate(
                            event, planned_tokens=estimate_per_prediction.total_tokens,
                            price_per_token=price_per_token,
                        ),
                    }, sort_keys=True)}
                repository.record_model_event(action, event, owner_kind=TASK, owner_id=digest)
                if action == "finish":
                    for name in ("input_tokens", "output_tokens", "cost"):
                        if event.get(name) is not None:
                            usage[name] = max(usage.get(name, 0), event[name])

            with budget.request(replace(estimate_per_prediction, candidates=1)) as charge:
                with observe_model_calls(observe):
                    try:
                        # Root guarantees a receipt even for a simple fake callback.
                        client = SimpleNamespace(model=model, provider="offline_explicit")
                        with model_call(client, purpose=TASK, prompt=request):
                            raw = dict(predict(request))
                    finally:
                        tokens = sum(usage.get(name, 0) for name in ("input_tokens", "output_tokens"))
                        cost = usage.get("cost")
                        if tokens and estimate_per_prediction.total_tokens and estimate_per_prediction.estimated_usd is not None:
                            cost = max(cost or 0., tokens * estimate_per_prediction.estimated_usd / estimate_per_prediction.total_tokens)
                        if subscription and estimate_per_prediction.estimated_usd is None:
                            cost = None  # estimated tokens only; never refused
                        charge.reconcile(total_tokens=tokens or None, estimated_usd=cost)
            try:
                probability = _probability(raw)
            except ValueError:
                probability = None
            with repository.connection() as connection:
                judgment_id = append_judgment(
                    connection, task=TASK, left_kind="offline_prediction", left_id=digest,
                    judge="llm", judge_model=model, prompt_version=PROMPT_VERSION,
                    input_hash=digest, verdict=json.dumps(raw, sort_keys=True),
                    score=probability,
                )
            if probability is None:
                summary["invalid"] += 1
                continue
            checkpoint = {"model": model, "input_hash": digest, "prompt_version": PROMPT_VERSION,
                          "settings_hash": _hash(settings or {}),
                          "p_success": probability, "judgment_id": judgment_id}
            # One completed prediction per checkpoint; interruptions never corrupt
            # a previously completed cache entry.
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(checkpoint, sort_keys=True), encoding="utf-8")
            temporary.replace(path)
            probabilities[digest] = probability
    except AIInterrupted:
        summary["status"] = "cancelled"
    except SpendLimitExceeded:
        summary["status"] = "over_budget"
    finally:
        summary["charged"] = asdict(budget.used)
    if len(probabilities) != len(requests):
        if summary["status"] == "complete":
            summary["status"] = "incomplete"
        return None, summary
    return CachedProbabilityArm(probabilities, model=model, settings=settings), summary
