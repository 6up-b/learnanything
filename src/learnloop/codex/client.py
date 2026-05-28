from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing import Literal, Protocol

from pydantic import BaseModel

from learnloop.config import CodexConfig
from learnloop.codex.prompts import AUTHORING_PROMPT_VERSION, CANONICAL_INGEST_PROMPT_VERSION, GRADING_PROMPT_VERSION
from learnloop.codex.schemas import AuthoringProposal, GradingProposal

LOG = logging.getLogger(__name__)
EVENT_FIELDS_ATTR = "event_fields"

SourceKind = Literal["website_page", "youtube_video", "arxiv_html", "textbook_chapter"]
ChunkKind = Literal["prose", "heading", "code", "math", "caption"]


@dataclass(frozen=True)
class AuthoringContext:
    vault_root: str
    source_ids: list[str]
    instructions: str | None = None
    subjects: list[str] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    practice_items: list[dict] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class SourceChunk:
    """A bounded slice of normalized source Markdown with a stable locator.

    ``locator`` is content-derived and stable across re-fetches (see the spec's
    locator-stability rules); Codex echoes it back in ``SourceRef.locator`` so
    extracted items resolve to a specific span of the registered source.
    """

    locator: str
    text: str
    chunk_kind: ChunkKind = "prose"
    heading_path: list[str] = field(default_factory=list)
    label: str | None = None
    ordinal: int = 0


@dataclass(frozen=True)
class ExtractionPlan:
    """Ordered plan handed to the canonical-ingestor role.

    Learning Objects are created first, then Practice Items, concept edges, and
    rubric drafts attach to them. ``learning_object_required`` is ``False`` only
    in textbook-anchored mode, where retrieving practice for the supplied LOs is
    the primary output and new LOs are gap proposals.
    """

    create_learning_objects_first: bool = True
    attach_practice_items: bool = True
    attach_concept_edges: bool = True
    attach_rubric_drafts: bool = True
    allow_generative_practice_items: bool = True
    require_source_ref_per_item: bool = True
    learning_object_required: bool = True


@dataclass(frozen=True)
class CanonicalIngestContext:
    """Bounded, deterministic input for ``run_canonical_ingest``.

    LearnLoop fetches, normalizes, hashes, and registers the source before
    building this context; Codex only performs semantic extraction over the
    supplied chunks and never fetches URLs or writes files. ``canonical_source``
    is a descriptor of the already-registered canonical-source note: ``id``,
    ``path``, ``canonical_uri``, ``original_uri``, ``title``, ``authors``,
    ``content_hash``, ``retrieved_at``, and ``license_hint``.
    """

    vault_root: str
    source_kind: SourceKind
    canonical_source: dict
    chunks: list[SourceChunk]
    target_subject: str | None = None
    target_learning_object_ids: list[str] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    extraction_plan: ExtractionPlan = field(default_factory=ExtractionPlan)
    instructions: str | None = None


@dataclass(frozen=True)
class GradingContext:
    attempt_id: str
    practice_item_id: str
    prompt: str
    expected_answer: str
    learner_answer_md: str
    rubric: dict
    evidence_facets: list[str] = field(default_factory=list)
    evidence_weights: dict[str, float] = field(default_factory=dict)
    criterion_facet_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    error_taxonomy: dict[str, Any] = field(default_factory=dict)


class CodexClient(Protocol):
    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...


class CodexUnavailable(RuntimeError):
    pass


def make_codex_client(config: CodexConfig, vault_root: Path) -> CodexClient:
    provider = config.provider.lower()
    if provider == "http":
        return HttpCodexClient(config)
    if provider == "sdk":
        return SdkCodexClient(config, vault_root)
    raise CodexUnavailable(f"Unsupported Codex provider {config.provider!r}")


class HttpCodexClient:
    """Minimal local Codex app-server client.

    The MVP transport is intentionally small: JSON POSTs to a local app-server.
    The server may return the proposal directly or under a top-level
    ``proposal`` key.
    """

    def __init__(self, config: CodexConfig):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "http_adapter"
        self.model = config.model

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        payload = self._post(self.config.authoring_path, {"context": asdict(context)}, purpose="authoring")
        return AuthoringProposal.model_validate(payload.get("proposal", payload))

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        payload = self._post(
            self.config.canonical_ingest_path,
            {"context": asdict(context)},
            purpose="canonical_ingest",
        )
        return AuthoringProposal.model_validate(payload.get("proposal", payload))

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        payload = self._post(self.config.grading_path, {"context": asdict(context)}, purpose="grading")
        return GradingProposal.model_validate(payload.get("proposal", payload))

    def _post(self, path: str, payload: dict, *, purpose: str) -> dict:
        url = _url(self.config.base_url, path)
        _log_codex_debug(
            "codex.http.request",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            request_payload=payload,
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.healthcheck_timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=f"HTTP {exc.code}",
            )
            raise CodexUnavailable(f"Codex app-server HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=str(exc.reason),
            )
            raise CodexUnavailable(str(exc.reason)) from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response_text=_decode_lossy(raw),
                error="invalid_json",
            )
            raise CodexUnavailable("Codex app-server returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response=decoded,
                error="non_object_response",
            )
            raise CodexUnavailable("Codex app-server response must be a JSON object")
        _log_codex_debug(
            "codex.http.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            response=decoded,
        )
        return decoded


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _decode_lossy(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


class SdkCodexClient:
    """Codex Python SDK-backed client.

    The SDK speaks the real Codex app-server v2 JSON-RPC protocol over stdio.
    LearnLoop still owns the learning-specific schemas and validates the final
    model output before anything can be persisted.
    """

    def __init__(self, config: CodexConfig, vault_root: Path):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "codex_sdk"
        self.model = config.model
        self.vault_root = vault_root.resolve()
        self.checkout_path = _resolve_checkout_path(self.vault_root, config.checkout_path)
        self.sdk_python_path = _resolve_sdk_python_path(self.checkout_path, config.sdk_python_path)

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        text = self._run_structured(
            _authoring_prompt(context),
            _codex_output_schema(AuthoringProposal),
            purpose="authoring",
        )
        return AuthoringProposal.model_validate_json(text)

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        text = self._run_structured(
            _canonical_ingest_prompt(context),
            _codex_output_schema(AuthoringProposal),
            purpose="canonical_ingest",
        )
        return AuthoringProposal.model_validate_json(text)

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        text = self._run_structured(
            _grading_prompt(context),
            _codex_output_schema(GradingProposal),
            purpose="grading",
        )
        return GradingProposal.model_validate_json(text)

    def _run_structured(self, prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        _ensure_sdk_importable(self.sdk_python_path)
        try:
            from openai_codex import Codex
            from openai_codex.client import AppServerConfig
            from openai_codex.types import Personality, ReasoningEffort, ReasoningSummary
        except ImportError as exc:
            raise CodexUnavailable(
                f"Codex Python SDK is not importable from {self.sdk_python_path}."
            ) from exc

        try:
            effort = _sdk_reasoning_effort(ReasoningEffort, self.config.reasoning_effort)
            summary = _sdk_reasoning_summary(ReasoningSummary, self.config.reasoning_summary)
            launch_args = _sdk_launch_args(self.config.sdk_launch_command)
            if launch_args is None and not self.config.sdk_codex_bin:
                launch_args = _default_sdk_launch_args()
            app_config = AppServerConfig(
                codex_bin=self.config.sdk_codex_bin or None,
                launch_args_override=launch_args,
                cwd=str(self.vault_root),
                client_name="learnloop",
                client_title="LearnLoop",
            )
            _log_codex_debug(
                "codex.prompt",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=str(self.vault_root),
                service_name=f"learnloop:{purpose}",
                reasoning_effort=self.config.reasoning_effort,
                reasoning_summary=self.config.reasoning_summary,
                prompt=prompt,
                prompt_length=len(prompt),
                output_schema=output_schema,
            )
            with Codex(config=app_config) as codex:
                thread = codex.thread_start(
                    cwd=str(self.vault_root),
                    model=self.config.model or None,
                    service_name=f"learnloop:{purpose}",
                )
                result = thread.run(
                    prompt,
                    cwd=str(self.vault_root),
                    model=self.config.model or None,
                    effort=effort,
                    output_schema=output_schema,
                    personality=Personality.pragmatic,
                    summary=summary,
                )
        except Exception as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=str(self.vault_root),
                error=str(exc),
            )
            raise CodexUnavailable(str(exc)) from exc

        final_response = result.final_response
        _log_codex_debug(
            "codex.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            cwd=str(self.vault_root),
            response=final_response,
            response_length=len(final_response) if final_response is not None else None,
        )
        if final_response is None:
            raise CodexUnavailable("Codex SDK turn completed without a final response.")
        return final_response.strip()


# Difficulty estimation guidance threaded into both authoring prompts so the 2PL
# difficulty `b` (spec_irt_difficulty.md §4.3, §6.3) is populated on ship.
_DIFFICULTY_GUIDANCE = (
    "Estimate `difficulty` for every Practice Item and `difficulty_prior` for every "
    "Learning Object on this [0,1] anchor scale: 0.0-0.2 trivial/recognition, "
    "0.2-0.4 easy recall, 0.4-0.5 basic application, 0.5 normal target-level, "
    "0.6-0.8 transfer/multi-step, 0.8-1.0 difficult synthesis/adversarial. "
    "Set `difficulty_source = \"llm_estimate\"` on every item you estimate."
)

_PRACTICE_METADATA_GUIDANCE = (
    "For every generated Practice Item, include reward-facing metadata: "
    "`evidence_facets`, `evidence_weights`, `criterion_facet_weights` when a rubric "
    "exists, `retrieval_demand`, `transfer_distance`, `scaffold_level`, "
    "`surface_family`, and `repair_targets`. `repair_targets` must name evidence "
    "facets or rubric fatal error ids."
)


def _authoring_prompt(context: AuthoringContext) -> str:
    return _json_prompt(
        "learnloop authoring proposal",
        AUTHORING_PROMPT_VERSION,
        {
            "task": (
                "Create a LearnLoop AuthoringProposal for useful Learning Objects, "
                "Practice Items, concept edges, or rubric updates. Persist nothing; "
                "return only schema-valid JSON. "
                + _DIFFICULTY_GUIDANCE
                + " "
                + _PRACTICE_METADATA_GUIDANCE
            ),
            "context": asdict(context),
        },
    )


def _canonical_ingest_prompt(context: CanonicalIngestContext) -> str:
    return _json_prompt(
        "learnloop canonical source ingestion",
        CANONICAL_INGEST_PROMPT_VERSION,
        {
            "task": (
                "Extract source-grounded LearnLoop authoring proposal items from the "
                "provided canonical-source chunks. Use the supplied source locators "
                "for source refs. Return only schema-valid JSON. "
                + _DIFFICULTY_GUIDANCE
                + " "
                + _PRACTICE_METADATA_GUIDANCE
            ),
            "context": asdict(context),
        },
    )


def _grading_prompt(context: GradingContext) -> str:
    return _json_prompt(
        "learnloop grading proposal",
        GRADING_PROMPT_VERSION,
        {
            "task": (
                "Grade the learner answer against the prompt, expected answer, and "
                "rubric. Return a LearnLoop GradingProposal as schema-valid JSON only. "
                "Use the supplied canonical error taxonomy for ordinary errors: "
                "`recall_failure`, `conceptual_slip`, `procedure_misapplication`, "
                "`arithmetic_slip`, or `incomplete_answer`. Use existing rubric fatal "
                "error ids or vault-specific taxonomy ids only when they apply more "
                "precisely. If the learner explicitly says they do not know, do not "
                "remember, or cannot recall a specific requested part, assign that "
                "part as `recall_failure`; do not invent a `missing_*` or `unknown_*` "
                "error type. For each failed rubric line or facet, add an "
                "error_attribution unless another attribution already covers the same "
                "failure. For each error_attribution, fill "
                "`target_criterion_ids` and/or `target_evidence_families` with "
                "the rubric line(s) and item evidence facet(s) most directly affected. "
                "Use the supplied `error_taxonomy.selection_policy` and "
                "`error_taxonomy.targeting_policy` exactly."
            ),
            "context": asdict(context),
        },
    )


def _json_prompt(title: str, prompt_version: str, payload: dict[str, Any]) -> str:
    return (
        f"{title}\n"
        f"prompt_version: {prompt_version}\n\n"
        "Return only JSON that matches the provided output schema. Do not include "
        "Markdown fences or explanatory prose.\n\n"
        f"{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    )


def _sdk_reasoning_effort(reasoning_effort_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_effort_type(normalized)
    except ValueError as exc:
        valid = ", ".join(item.value for item in reasoning_effort_type)
        raise CodexUnavailable(f"Invalid codex.reasoning_effort {value!r}; expected one of: {valid}") from exc


def _sdk_reasoning_summary(reasoning_summary_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_summary_type.model_validate(normalized)
    except Exception as exc:
        raise CodexUnavailable(
            f"Invalid codex.reasoning_summary {value!r}; expected none, auto, concise, or detailed"
        ) from exc


_UNSUPPORTED_STRICT_SCHEMA_KEYS = {
    "default",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "multipleOf",
    "pattern",
    "title",
    "uniqueItems",
}


def _codex_output_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return a schema accepted by Codex's strict Responses API wrapper."""

    return _strict_json_schema(model.model_json_schema())


def _strict_json_schema(value: Any) -> Any:
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            normalized[key] = {name: _strict_json_schema(schema) for name, schema in child.items()}
            continue
        if key in _UNSUPPORTED_STRICT_SCHEMA_KEYS:
            continue
        if key == "additionalProperties":
            continue
        normalized[key] = _strict_json_schema(child)

    if _is_object_schema(normalized):
        properties = normalized.get("properties")
        if isinstance(properties, dict):
            normalized["required"] = list(properties.keys())
        else:
            normalized.setdefault("required", [])
        normalized["additionalProperties"] = False

    return normalized


def _is_object_schema(schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    if schema_type == "object":
        return True
    if isinstance(schema_type, list) and "object" in schema_type:
        return True
    return "properties" in schema


def _ensure_sdk_importable(sdk_python_path: Path) -> None:
    if sdk_python_path.exists():
        value = str(sdk_python_path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _sdk_launch_args(command: str) -> tuple[str, ...] | None:
    if not command.strip():
        return None
    return tuple(shlex.split(command, posix=os.name != "nt"))


def _default_sdk_launch_args() -> tuple[str, ...]:
    executable = shutil.which("codex.cmd" if os.name == "nt" else "codex") or "codex"
    return (executable, "app-server", "--listen", "stdio://")


def _resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path:
    raw = Path(checkout_path)
    if raw.is_absolute():
        return raw.resolve()
    return (vault_root / raw).resolve()


def _resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path:
    raw = Path(sdk_python_path)
    if raw.is_absolute():
        return raw.resolve()
    return (checkout_path / raw).resolve()


def _log_codex_debug(event: str, **fields: Any) -> None:
    """Emit full Codex request/response data into sidecar debug logs.

    The sidecar JSONL formatter treats ``event_fields`` specially. Keeping this
    helper in the core client avoids coupling Codex transport code back to the
    Tauri sidecar package while still making debug logs capture each prompt and
    response when sidecar debug logging is enabled.
    """

    if not LOG.isEnabledFor(logging.DEBUG):
        return
    LOG.debug(event, extra={EVENT_FIELDS_ATTR: {k: v for k, v in fields.items() if v is not None}})
