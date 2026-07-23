"""Demand-paged synthesis: reader background requests (spec §6, design B step 6).

The reading hot path NEVER calls a model. ``enqueue_request`` resolves the smallest
sufficient neighborhood (§6.3), computes the durable idempotency key over the exact
revision + model contract (§6.2), and writes ONE ``queued`` row. A separate worker
(``drain_requests``) claims rows under a fenced lease (migration-080 precedent),
synthesizes within owner-reviewed bounds, and lands results as REVIEWABLE proposals
(proposed source objects + canonical mapping proposals) that are NEVER auto-admitted
into pools or evidence (§6.4). Cancelling a request never cancels the local capture.

Same contract reuses a standing/completed result; a material version change (model,
schema, revision) mints a successor request (§15.3). Reader requests take an
interactive priority band above bulk but bounded so scrolling cannot starve a batch.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping

from learnloop.clock import Clock, utc_now_iso, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services import source_objects as SO

# ---------------------------------------------------------------------------
# Decision parameters (registered at birth in parameter_registry §E). Numeric
# module constants -> AST-audited: keep the numeric set to exactly these three.
# ---------------------------------------------------------------------------

# §6.3 interactive priority above bulk jobs, starvation-bounded.
PRIORITY_BAND = 10
# §6.3 smallest-sufficient-window: max adjacent blocks on EACH side of the target.
MAX_ADJACENT_BLOCKS = 2
# §6.3 per-request token cap (visible); exceeding keeps the capture + offers manual.
TOKEN_CAP = 6000

# Non-numeric contract versions (not decision params).
INVENTORY_SCHEMA_VERSION = "reader-inventory-v1"
SYNTHESIS_SCHEMA_VERSION = "reader-synthesis-v1"
PROMPT_VERSION = "reader-demand-paged-v1"
_chars_per_token = 4

# preset -> proposed source-object type for the demand-paged synthesis result.
_PRESET_OBJECT_TYPE: dict[str, str] = {
    "worked_example": "worked_example",
    "alt_explanation": "claim",
    "why_matters": "claim",
    "ask": "claim",
    "test_me_later": "claim",
    "help_me_remember": "claim",
    "connect_it": "claim",
    "mark_confusing": "claim",
}


class ReaderRequestError(ValueError):
    """Domain error for the demand-paged synthesis service."""


def neighborhood(repository: Repository, *, extraction_id: str, span_id: str) -> dict[str, Any]:
    """Resolve the smallest sufficient window (§6.3): the exact block, its enclosing
    heading/section, up to ``MAX_ADJACENT_BLOCKS`` adjacent blocks per side, and cited
    assets -- never unrelated chapter content."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderRequestError(f"extraction has no IR: {extraction_id!r}")
    blocks = sorted(ir.blocks, key=lambda b: b.ordinal)
    idx = next((i for i, b in enumerate(blocks) if b.span_id == span_id), None)
    if idx is None:
        raise ReaderRequestError(f"unknown span: {span_id!r}")
    target = blocks[idx]
    section_path = list(target.section_path)
    lo = max(0, idx - MAX_ADJACENT_BLOCKS)
    hi = min(len(blocks), idx + MAX_ADJACENT_BLOCKS + 1)
    window = blocks[lo:hi]
    # Keep only blocks that share the enclosing section (no unrelated chapter).
    kept = [b for b in window if list(b.section_path)[: len(section_path)] == section_path] or [target]
    span_ids = [b.span_id for b in kept]
    assets = sorted({a for b in kept for a in b.asset_ids})
    text = "\n\n".join(b.text for b in kept)
    return {
        "span_ids": span_ids,
        "section_path": section_path,
        "assets": assets,
        "adjacent_count": len(kept) - 1,
        "text": text,
        "char_count": len(text),
    }


def request_key(
    *,
    revision_id: str,
    window: Mapping[str, Any],
    preset: str,
    provider: str,
    model: str,
    config_hash: str,
    inventory_profile: str = "semantic",
) -> str:
    """Canonical idempotency key over {revision, window, preset, inventory schema +
    profile, synthesis/output schema, prompt+provider+model, config/policy} (§6.2).
    Keyed on the REVISION -- not a mutable 'current source'."""

    canonical = json.dumps(
        {
            "revision_id": revision_id,
            "span_ids": window.get("span_ids", []),
            "preset": preset,
            "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
            "inventory_profile": inventory_profile,
            "synthesis_schema_version": SYNTHESIS_SCHEMA_VERSION,
            "prompt_version": PROMPT_VERSION,
            "provider": provider,
            "model": model,
            "config_hash": config_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def enqueue_request(
    repository: Repository,
    *,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    span_id: str,
    preset: str,
    provider: str = "stub",
    model: str = "stub-1",
    config_hash: str = "",
    inventory_profile: str = "semantic",
    annotation_id: str | None = None,
    commitment_id: str | None = None,
    client_idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Enqueue a demand-paged synthesis request (§6). Idempotent on the canonical
    request key; returns visible scope + token/cap metadata (§6.3). The reading path
    never blocks on this -- it only writes a durable ``queued`` row."""

    window = neighborhood(repository, extraction_id=extraction_id, span_id=span_id)
    key = request_key(
        revision_id=revision_id, window=window, preset=preset,
        provider=provider, model=model, config_hash=config_hash,
        inventory_profile=inventory_profile,
    )
    est_input = window["char_count"] // _chars_per_token + 1
    est_output = 512
    capped = (est_input + est_output) > TOKEN_CAP

    existing = repository.reader_request_by_key(key)
    result = repository.enqueue_reader_request(
        request_key=key,
        fields={
            "source_id": source_id,
            "revision_id": revision_id,
            "extraction_id": extraction_id,
            "span_id": span_id,
            "window": window,
            "preset": preset,
            "action": preset,
            "inventory_profile": inventory_profile,
            "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
            "synthesis_schema_version": SYNTHESIS_SCHEMA_VERSION,
            "prompt_version": PROMPT_VERSION,
            "provider": provider,
            "model": model,
            "config_hash": config_hash,
            "priority_band": PRIORITY_BAND,
            "est_input_tokens": est_input,
            "est_output_tokens": est_output,
            "token_cap": TOKEN_CAP,
            "reason": "token_cap_exceeded" if capped else None,
            "annotation_id": annotation_id,
            "commitment_id": commitment_id,
            "client_idempotency_key": client_idempotency_key,
        },
        clock=clock,
    )
    row = repository.get_reader_request(result["id"]) or {}
    # Reuse a standing/completed result: cache hit when the contract already ran.
    cache_hit = bool(existing is not None and existing.get("status") == "complete")
    return {
        "request_id": result["id"],
        "request_key": key,
        "deduplicated": result["deduplicated"],
        "cache_hit": cache_hit,
        "status": row.get("status", "queued"),
        "scope": {
            "span_ids": window["span_ids"],
            "section_path": window["section_path"],
            "assets": window["assets"],
            "adjacent_blocks": window["adjacent_count"],
        },
        "est_input_tokens": est_input,
        "est_output_tokens": est_output,
        "token_cap": TOKEN_CAP,
        "cap_remaining": TOKEN_CAP - (est_input + est_output),
        "capped": capped,
        "provider": provider,
        "model": model,
    }


def request_status(repository: Repository, *, request_id: str) -> dict[str, Any] | None:
    row = repository.get_reader_request(request_id)
    if row is None:
        return None
    out = dict(row)
    for jkey in ("window_json", "result_json", "error_json"):
        raw = out.get(jkey)
        if isinstance(raw, str) and raw:
            try:
                out[jkey.removesuffix("_json")] = json.loads(raw)
            except ValueError:
                pass
    return out


def cancel_request(repository: Repository, *, request_id: str, clock: Clock | None = None) -> dict[str, Any] | None:
    return repository.cancel_reader_request(request_id, clock=clock)


def retry_request(repository: Repository, *, request_id: str, clock: Clock | None = None) -> dict[str, Any] | None:
    return repository.retry_reader_request(request_id, clock=clock)


def _land_proposals(
    repository: Repository,
    request: Mapping[str, Any],
    clock: Clock | None,
    *,
    object_type: str,
    exact_text: str,
    content: Mapping[str, Any],
    span_ids: list[str],
    model_provenance: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Land one synthesis result as the reviewable §6.4 artifact pair: a PROPOSED
    source object + canonical mapping proposal (+ commitment mapping for
    commit-class presets). Never auto-admitted."""

    authored = SO.author_source_object(
        repository,
        source_id=request["source_id"],
        revision_id=request["revision_id"],
        object_type=object_type,
        exact_text=exact_text,
        content=dict(content),
        citations=[{"revision_id": request["revision_id"], "span_id": sid} for sid in span_ids],
        authorship="ai",
        status="proposed",
        model_provenance=dict(model_provenance),
        clock=clock,
    )
    mapping = SO.propose_mapping(
        repository,
        target_kind="new_object",
        source_object_id=authored["source_object_id"],
        annotation_id=request.get("annotation_id"),
        confidence=0.5,
        rationale=f"demand-paged synthesis for reader preset {request.get('preset')!r}",
        provenance={"request_key": request.get("request_key"), "revision_id": request.get("revision_id")},
        clock=clock,
    )
    proposals = [
        {"kind": "source_object", "source_object_id": authored["source_object_id"], "object_type": object_type},
        {"kind": "canonical_mapping", "proposal_id": mapping["proposal_id"]},
    ]
    if request.get("commitment_id"):
        commit_map = SO.propose_mapping(
            repository, target_kind="commitment",
            source_object_id=authored["source_object_id"],
            target_ref=request["commitment_id"], confidence=0.5,
            rationale="reader commit preset relationship", clock=clock,
        )
        proposals.append({"kind": "canonical_mapping", "proposal_id": commit_map["proposal_id"]})
    return proposals


def model_synthesis(client: Any) -> Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]]:
    """Build the real ``synthesize`` seam for :func:`drain_requests`.

    The model output is candidate-only: span citations are validated against
    the request's own window and the content lands as a PROPOSED source object
    (§6.4). A provider lacking ``run_reader_preset_synthesis`` raises so the
    request resolves ``failed`` (retryable) — stub content is never presented
    as synthesized."""

    def synthesize(
        repository: Repository, request: Mapping[str, Any], clock: Clock | None
    ) -> dict[str, Any]:
        run_preset = getattr(client, "run_reader_preset_synthesis", None)
        if run_preset is None:
            raise ReaderRequestError(
                "The configured AI provider does not support reader preset synthesis."
            )
        window = json.loads(request.get("window_json") or "{}")
        span_ids = [str(s) for s in window.get("span_ids") or []]
        ir = repository.load_document_ir(request["extraction_id"])
        if ir is None:
            raise ReaderRequestError(f"extraction has no IR: {request['extraction_id']!r}")
        blocks = [
            {"span_id": block.span_id, "text": " ".join((block.text or "").split())}
            for block in sorted(ir.blocks, key=lambda b: b.ordinal)
            if block.span_id in set(span_ids)
        ]
        if not blocks:
            raise ReaderRequestError("request window resolves to no readable blocks")

        learner_text = ""
        annotation_id = request.get("annotation_id")
        if annotation_id:
            head = repository.annotation_head(annotation_id)
            version = (head or {}).get("version") or {}
            learner_text = str(version.get("learner_text") or "")

        from learnloop.codex.client import ReaderPresetSynthesisContext

        result = run_preset(ReaderPresetSynthesisContext(
            preset=str(request.get("preset") or ""),
            learner_text=learner_text,
            section_path=list(window.get("section_path") or []),
            blocks=blocks,
        ))
        content_md = (result.content_md or "").strip()
        if not content_md:
            raise ReaderRequestError("the model returned empty preset content")
        valid = {block["span_id"] for block in blocks}
        cited = [sid for sid in result.span_ids if sid in valid]
        if not cited:
            raise ReaderRequestError(
                f"the model cited no valid window spans: {list(result.span_ids)!r}"
            )

        preset = str(request.get("preset") or "")
        proposals = _land_proposals(
            repository, request, clock,
            object_type=_PRESET_OBJECT_TYPE.get(preset, "claim"),
            exact_text=(window.get("text") or "").strip()[:2000],
            content={
                "preset": preset,
                "content_md": content_md,
                "section_path": window.get("section_path", []),
            },
            span_ids=cited,
            # Provenance names the client that actually ran, not the enqueue-time
            # placeholder ("stub") the request row may carry.
            model_provenance={
                "provider": getattr(getattr(client, "config", None), "provider", None)
                or getattr(client, "provider_name", None)
                or request.get("provider"),
                "model": getattr(getattr(client, "config", None), "model", None)
                or getattr(client, "model", None)
                or request.get("model"),
                "prompt_version": PROMPT_VERSION,
            },
        )
        return {
            "proposals": proposals,
            "tokens_in": window.get("char_count", 0) // _chars_per_token,
            "tokens_out": max(128, len(content_md) // _chars_per_token),
        }

    return synthesize


def _deterministic_synthesis(
    repository: Repository, request: Mapping[str, Any], clock: Clock | None
) -> dict[str, Any]:
    """Deterministic, no-LLM synthesis producing a PROPOSED source object + canonical
    mapping proposal (the reviewable artifact, §6.4). Used as the default seam and as
    the test stub; a real client is injected via ``synthesize``."""

    window = json.loads(request.get("window_json") or "{}")
    preset = request.get("preset", "")
    span_ids = window.get("span_ids") or ([request["span_id"]] if request.get("span_id") else [])
    text = (window.get("text") or "").strip()
    proposals = _land_proposals(
        repository, request, clock,
        object_type=_PRESET_OBJECT_TYPE.get(preset, "claim"),
        exact_text=text[:2000],
        content={"preset": preset, "section_path": window.get("section_path", [])},
        span_ids=[str(sid) for sid in span_ids],
        model_provenance={"provider": request.get("provider"), "model": request.get("model"),
                          "prompt_version": request.get("prompt_version")},
    )
    return {"proposals": proposals, "tokens_in": window.get("char_count", 0) // _chars_per_token,
            "tokens_out": 128}


def drain_requests(
    repository: Repository,
    *,
    worker_id: str = "reader-synth",
    lease_seconds: int = 120,
    limit: int = 100,
    synthesize: Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Drain queued requests under a fenced lease. Results land as reviewable
    proposals; NEVER auto-admitted (§6.4). A capped request resolves ``partial`` with
    the visible reason and produces no synthesis (§6.3, no silent scope expansion)."""

    synth = synthesize or _deterministic_synthesis
    completed: list[str] = []
    failed: list[str] = []
    partial: list[str] = []
    for _ in range(limit):
        now = utc_now_iso(clock)
        expires = _plus_seconds(now, lease_seconds)
        request = repository.claim_next_reader_request(
            worker_id=worker_id, now_iso=now, lease_expires_at=expires, lease_cutoff_iso=now
        )
        if request is None:
            break
        epoch = request["lease_epoch"]
        if request.get("cancel_requested"):
            repository.resolve_reader_request(
                request_id=request["id"], status="cancelled", expected_lease_epoch=epoch, clock=clock
            )
            continue
        if request.get("reason") == "token_cap_exceeded":
            repository.resolve_reader_request(
                request_id=request["id"], status="partial",
                result={"reason": "token_cap_exceeded", "offer": "local_or_manual"},
                expected_lease_epoch=epoch, clock=clock,
            )
            partial.append(request["id"])
            continue
        try:
            result = synth(repository, request, clock)
            repository.resolve_reader_request(
                request_id=request["id"], status="complete", result=result,
                actual_input_tokens=int(result.get("tokens_in", 0)),
                actual_output_tokens=int(result.get("tokens_out", 0)),
                expected_lease_epoch=epoch, clock=clock,
            )
            completed.append(request["id"])
        except Exception as exc:  # noqa: BLE001 - capture retained; request stays retryable
            repository.resolve_reader_request(
                request_id=request["id"], status="failed", error={"message": str(exc)},
                expected_lease_epoch=epoch, clock=clock,
            )
            failed.append(request["id"])
    return {"completed": completed, "failed": failed, "partial": partial}


def _plus_seconds(now_iso: str, seconds: int) -> str:
    from datetime import timedelta

    return (parse_utc(now_iso) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
