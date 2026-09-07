"""Start-screen epigraphs: quotes and haiku about freshly synthesized material.

Once per completed bootstrap or append synthesis, the same canonical-ingest
client that authored the map writes three short epigraphs about it — a
one-line aphorism in the spirit of the Start screen's "Escape will make me ..."
hero line, or a three-line haiku — and they are appended to ``vault_epigraphs``
(migration 158) for the desktop Start screen to cycle.

Best-effort by contract: :func:`generate_vault_epigraphs` never raises and never
changes the outcome of the paid synthesis it follows. A manifest cache hit
(``reused=True``) and candidate revalidation produce no epigraphs — no new
material was synthesized. Validation is in code, never trusted from the model:
kind, line counts, length caps, and a dedupe against the subject's recent rows.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.ai.usage import consume_client_usage
from learnloop.clock import Clock
from learnloop.content.synthesis.ai_contracts import (
    VAULT_EPIGRAPHS_PROMPT_VERSION,
    VaultEpigraph,
    VaultEpigraphBatch,
    VaultEpigraphContext,
    vault_epigraphs_prompt,
)
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

logger = logging.getLogger(__name__)

EPIGRAPH_PURPOSE = "vault_epigraphs"
EPIGRAPHS_PER_SYNTHESIS = 3
EPIGRAPH_KINDS = ("quote", "haiku")
QUOTE_MAX_WORDS = 12
QUOTE_MAX_CHARS = 120
HAIKU_LINES = 3
HAIKU_LINE_MAX_WORDS = 10
HAIKU_LINE_MAX_CHARS = 60
MAX_DIGEST_CONCEPTS = 24
MAX_DIGEST_CLAIMS = 24
MAX_DIGEST_LEARNING_OBJECTS = 16
MAX_DIGEST_ITEM_CHARS = 200
MAX_SUMMARY_CHARS = 600
RECENT_FOR_DEDUPE = 50
RECENT_IN_PROMPT = 12
_BRIEF_KEYS = ("outcome", "depth", "scope", "intent_sentence", "goal_title", "starting_level")
_WRAPPING_QUOTES = "\"'“”‘’«»"
_MARKDOWN_LEAD = re.compile(r"^(?:[-–—*#>•]|\d+[.)])\s")
# " — Someone Famous": an em/en dash followed only by capitalised words.
_ATTRIBUTION_TAIL = re.compile(r"\s[—–]\s*(?:[A-Z][\w'.]*\s?){1,4}$")
_WHITESPACE = re.compile(r"\s+")


def request_vault_epigraphs(
    client: StructuredTransport, context: VaultEpigraphContext
) -> VaultEpigraphBatch:
    """Author one epigraph batch through the shared transport (raw call)."""

    return execute_structured_operation(
        client,
        purpose=EPIGRAPH_PURPOSE,
        prompt=vault_epigraphs_prompt(context),
        result_model=VaultEpigraphBatch,
    )


# --- content digest ---------------------------------------------------------


@dataclass(frozen=True)
class ContentDigest:
    """What the model gets to write about: bounded, deduplicated titles/claims."""

    summary: str = ""
    concepts: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    learning_objects: list[str] = field(default_factory=list)


def digest_from_proposal_rows(
    rows: Iterable[Mapping[str, Any]], *, summary: str = ""
) -> ContentDigest:
    """Digest the proposal rows a synthesis persisted (bootstrap or the
    new_coverage part of an append)."""

    concepts: list[Any] = []
    claims: list[Any] = []
    learning_objects: list[Any] = []
    for row in rows:
        payload = row.get("payload") or {}
        if not isinstance(payload, Mapping):
            continue
        item_type = row.get("item_type")
        if item_type == "concept":
            concepts.append(payload.get("title"))
        elif item_type == "facet":
            claims.append(payload.get("claim"))
        elif item_type == "learning_object":
            learning_objects.append(payload.get("title"))
    return _digest(summary, concepts, claims, learning_objects)


def digest_for_append(
    rows: Iterable[Mapping[str, Any]],
    new_inventories: Iterable[Mapping[str, Any]] | None,
    neighborhood: Mapping[str, Any] | None,
    *,
    summary: str = "",
) -> ContentDigest:
    """An append may emit only provenance links, so top the row digest up
    from the new unit inventories and the bounded affected neighborhood."""

    base = digest_from_proposal_rows(rows, summary=summary)
    concepts: list[Any] = list(base.concepts)
    claims: list[Any] = list(base.claims)
    learning_objects: list[Any] = list(base.learning_objects)
    summary_text = base.summary
    for entry in new_inventories or []:
        inventory = entry.get("inventory") if isinstance(entry, Mapping) else None
        if not isinstance(inventory, Mapping):
            continue
        if not summary_text:
            summary_text = str(inventory.get("outline_summary") or "")
        claims.extend(_field_of(inventory.get("claims"), "statement"))
        concepts.extend(_field_of(inventory.get("concept_mentions"), "name"))
    hood = neighborhood if isinstance(neighborhood, Mapping) else {}
    concepts.extend(_field_of(hood.get("concepts"), "title"))
    claims.extend(_field_of(hood.get("facets"), "claim"))
    learning_objects.extend(_field_of(hood.get("learning_objects"), "title"))
    return _digest(summary_text, concepts, claims, learning_objects)


def _field_of(entries: Any, key: str) -> list[Any]:
    return [entry.get(key) for entry in (entries or []) if isinstance(entry, Mapping)]


def _digest(summary: Any, concepts: list[Any], claims: list[Any], learning_objects: list[Any]) -> ContentDigest:
    return ContentDigest(
        summary=_collapse(str(summary or ""))[:MAX_SUMMARY_CHARS],
        concepts=_bounded(concepts, MAX_DIGEST_CONCEPTS),
        claims=_bounded(claims, MAX_DIGEST_CLAIMS),
        learning_objects=_bounded(learning_objects, MAX_DIGEST_LEARNING_OBJECTS),
    )


def _bounded(values: Iterable[Any], cap: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _collapse(str(value or ""))[:MAX_DIGEST_ITEM_CHARS]
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= cap:
            break
    return out


def _collapse(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


# --- validation --------------------------------------------------------------


def normalize_epigraph(item: VaultEpigraph | Mapping[str, Any]) -> tuple[str, list[str]] | None:
    """``(kind, lines)`` for a well-formed epigraph, else None. Strips wrapping
    quotes and whitespace; rejects markdown-ish lines, URLs, attribution tails,
    and anything outside the quote/haiku shape."""

    data = item if isinstance(item, Mapping) else item.model_dump()
    kind = str(data.get("kind") or "")
    if kind not in EPIGRAPH_KINDS:
        return None
    lines: list[str] = []
    for raw in data.get("lines") or []:
        line = _collapse(str(raw)).strip(_WRAPPING_QUOTES + " ")
        if line:
            lines.append(line)
    if any(_rejected_line(line) for line in lines):
        return None
    if kind == "quote":
        if len(lines) != 1:
            return None
        (line,) = lines
        if len(line.split()) > QUOTE_MAX_WORDS or len(line) > QUOTE_MAX_CHARS:
            return None
    else:
        if len(lines) != HAIKU_LINES:
            return None
        if any(
            len(line.split()) > HAIKU_LINE_MAX_WORDS or len(line) > HAIKU_LINE_MAX_CHARS
            for line in lines
        ):
            return None
    return kind, lines


def _rejected_line(line: str) -> bool:
    lowered = line.lower()
    return (
        bool(_MARKDOWN_LEAD.match(line))
        or "http://" in lowered
        or "https://" in lowered
        or "`" in line
        or bool(_ATTRIBUTION_TAIL.search(line))
    )


def _dedupe_key(text: str) -> str:
    return _collapse(re.sub(r"[^\w\s]", "", text.casefold()))


# --- generation --------------------------------------------------------------


def generate_vault_epigraphs(
    repository: Repository,
    vault: LoadedVault,
    client: Any,
    *,
    subject_id: str,
    source_set_id: str | None,
    synthesis_run_id: str | None,
    mode: str,
    digest: ContentDigest,
    brief: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Author and persist one batch. Never raises: every failure (unready or
    legacy provider, invalid output, a repository error) is one warning log
    and an empty result, so the paid synthesis it follows is untouched."""

    try:
        return _generate(
            repository, vault, client,
            subject_id=subject_id, source_set_id=source_set_id,
            synthesis_run_id=synthesis_run_id, mode=mode, digest=digest,
            brief=brief, clock=clock,
        )
    except Exception as exc:  # noqa: BLE001 - decorative surface; never fails a synthesis
        logger.warning(
            "vault epigraphs skipped for %s (run %s): %s",
            subject_id, synthesis_run_id, exc, exc_info=True,
        )
        return []


def _generate(
    repository: Repository,
    vault: LoadedVault,
    client: Any,
    *,
    subject_id: str,
    source_set_id: str | None,
    synthesis_run_id: str | None,
    mode: str,
    digest: ContentDigest,
    brief: Mapping[str, Any] | None,
    clock: Clock | None,
) -> list[dict[str, Any]]:
    if client is None:
        return []
    recent = repository.recent_vault_epigraphs(subject_id=subject_id, limit=RECENT_FOR_DEDUPE)
    seen = {_dedupe_key(str(row.get("text") or "")) for row in recent}
    context = VaultEpigraphContext(
        subject_id=subject_id,
        source_set_id=source_set_id or "",
        mode=mode,
        subject_title=_subject_title(vault, subject_id),
        source_set_title=_source_set_title(vault, source_set_id),
        brief={
            key: value
            for key, value in (brief or {}).items()
            if key in _BRIEF_KEYS and isinstance(value, (str, int, float))
        },
        summary=digest.summary,
        concepts=list(digest.concepts),
        claims=list(digest.claims),
        learning_objects=list(digest.learning_objects),
        recent_epigraphs=[str(row.get("text") or "") for row in recent[:RECENT_IN_PROMPT]],
    )
    try:
        batch = request_vault_epigraphs(client, context)
    finally:
        # The synthesis already drained its own usage before this hook ran;
        # anything left in the accumulator is ours, and must not leak into the
        # client's next use.
        usage = consume_client_usage(client)

    accepted: list[dict[str, str]] = []
    for item in getattr(batch, "epigraphs", None) or []:
        normalized = normalize_epigraph(item)
        if normalized is None:
            continue
        kind, lines = normalized
        text = "\n".join(lines)
        key = _dedupe_key(text)
        if key in seen:
            continue
        seen.add(key)
        accepted.append({"kind": kind, "text": text})
        if len(accepted) >= EPIGRAPHS_PER_SYNTHESIS:
            break
    if not accepted:
        logger.info("vault epigraphs: nothing valid returned for %s (run %s)", subject_id, synthesis_run_id)
        return []

    ids = repository.insert_vault_epigraphs(
        subject_id=subject_id,
        source_set_id=source_set_id,
        synthesis_run_id=synthesis_run_id,
        mode=mode,
        epigraphs=accepted,
        prompt_version=VAULT_EPIGRAPHS_PROMPT_VERSION,
        provider=getattr(client, "provider_name", None) or getattr(client, "provider_type", None),
        model=getattr(client, "model", None),
        clock=clock,
    )
    logger.info(
        "vault epigraphs: %d persisted for %s (run %s; tokens in=%d out=%d)",
        len(ids), subject_id, synthesis_run_id,
        getattr(usage, "input_tokens", 0), getattr(usage, "output_tokens", 0),
    )
    wanted = set(ids)
    rows = repository.recent_vault_epigraphs(subject_id=subject_id, limit=len(ids) + RECENT_IN_PROMPT)
    return [row for row in rows if row["id"] in wanted]


def _subject_title(vault: LoadedVault, subject_id: str) -> str:
    subject = (getattr(vault, "subjects", None) or {}).get(subject_id)
    metadata = getattr(subject, "metadata", None)
    return str(getattr(metadata, "title", None) or getattr(subject, "title", None) or "")


def _source_set_title(vault: LoadedVault, source_set_id: str | None) -> str:
    for source_set in getattr(vault, "source_sets", None) or []:
        if getattr(source_set, "id", None) == source_set_id:
            return str(getattr(source_set, "title", None) or "")
    return ""


__all__ = [
    "ContentDigest",
    "EPIGRAPHS_PER_SYNTHESIS",
    "EPIGRAPH_PURPOSE",
    "digest_for_append",
    "digest_from_proposal_rows",
    "generate_vault_epigraphs",
    "normalize_epigraph",
    "request_vault_epigraphs",
]
