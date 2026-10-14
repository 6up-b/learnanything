"""The learner's latent state as one read model (spec_mcp_frontend_c1 §4).

``learning_context`` is what the chat frontend reads so that a ChatGPT or
Claude conversation sees the same learner the local app does: active
misconceptions and the candidates still in the holding pen, open hypotheses
with the evidence for and against them and the repairs tried, recurrence
groups, recent answer traces, open learner-text gaps and retention risks. It
reads the existing ledgers and writes nothing; no model is called.

It is built to be shared. Router R2a's ``LearnerStateCardV1`` gathers the same
sections for its model (``daily_plan.router_card`` on ``router/r2a``, not yet
on main when this was written); the field names of ``open_hypotheses`` and
``recent_answer_traces`` match the card's ``open_hypotheses`` and
``recent_work`` entries so the card can adopt this module (the convergence
task in docs/reviews/mcp-c1a.md). The open-hypothesis predicate is the daily
plan's own (``db.stores.daily_plans.open_learner_state_hypotheses``, the same
function R2a reads).

**Leakage rules (the card's G5, applied to every output):**

* no answer key, reference solution, rubric or hint is ever read into the
  output; free text that could quote a key (a diagnosis summary, a
  hypothesis or misconception statement, a correction, the learner's own
  answer) is dropped when it reproduces any key its item is known to have had
  (today's YAML and every assessment-contract snapshot, so the key an attempt
  was graded against counts after the item is edited: :class:`KeyBook`;
  ``tutor_qa.span_leaks_expected``, the tutor's own filter), and says so; an
  answer whose question has changed since, with no pinned contract to say
  which revision it answered, is withheld too;
* exam and held-out material (``exam_material.item_exam_status``, every
  provenance form), items reserved for an assessment or a held-out exam,
  items held by an open cold check or a repair's cold retry, and diagnostic
  probes (:func:`withheld_items`) keep their result but never show a question
  or an answer, and neither does a hypothesis or a recurrence group drawn
  from one of their answers; nor does an item the vault cannot read (deleted,
  or its file unreadable). When the predicates cannot be read, including a
  source-sets file the loader could not read or a vault snapshot that changed
  while it loaded (:func:`protection_issues`), no question or answer shows at
  all (fail closed);
* a grade held for review (THE predicate, ``held_grades``) is "held for
  review", never a score;
* a question is the prompt of the attempt's pinned assessment contract (the
  revision it was graded against), never today's edited prompt.

Nothing here is evidence: every label (assisted, cold, held) is read from the
ledger that owns it.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso

_LOG = logging.getLogger(__name__)

CONTEXT_VERSION = "learner_context_v1"
#: Text limits, the card's (``router.card``): an answer excerpt, a question, a statement.
EXCERPT_LIMIT = 400
STEM_LIMIT = 200
STATEMENT_LIMIT = 300
#: Retention: an item whose modelled recall now is below this is at risk.
RETENTION_TARGET = 0.8

WITHHELD_EXAM = "exam or held-out material"
WITHHELD_RESERVED = "reserved for an assessment"
WITHHELD_COLD = "a check waiting in the app"
WITHHELD_PROBE = "a diagnostic check"
WITHHELD_UNREADABLE = "the protection rules could not be read"
WITHHELD_UNKNOWN_ITEM = "its question could not be checked (not readable in the vault)"
KEY_WITHHELD = "withheld: it states the answer key"
KEYS_UNREADABLE = "withheld: the answer keys could not be read"
REVISION_UNKNOWN = "withheld: the question was edited since and the revision this answer was graded against is not recorded"
#: A loader issue the remote runtime adds when the vault's files changed while
#: it read them, or a protection-bearing file was caught mid-write (empty):
#: nothing read from that snapshot can say what is protected.
SNAPSHOT_UNSETTLED = "vault:snapshot_unsettled"
PROTECTION_UNKNOWN = "which material is protected could not be read: no question or answer is shown"

_EXAM_ATTEMPT_TYPES = frozenset({"exam_attempt", "exam_evidence"})
_PROBE_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe"})
_COLD_TASK_KINDS = ("cold_retry", "certification_cold_probe")


@dataclass(frozen=True)
class ContextLimits:
    traces: int = 12
    hypotheses: int = 20
    misconceptions: int = 20
    candidates: int = 20
    groups: int = 10
    gaps: int = 20
    risks: int = 15


@dataclass(frozen=True)
class Withheld:
    """Items whose question and answers never leave LearnLoop, and why.

    ``available`` False means the predicates could not be read: callers then
    show no question and no answer at all (fail closed). ``known_items`` are
    the items the vault holds: an item outside them (deleted, or its file
    unreadable) cannot be checked, so it is withheld too."""

    reasons: Mapping[str, str] = field(default_factory=dict)
    available: bool = True
    unknowns: tuple[str, ...] = ()
    known_items: frozenset[str] | None = None

    def reason(self, item_id: str | None) -> str | None:
        if not self.available:
            return WITHHELD_UNREADABLE
        key = str(item_id or "")
        found = self.reasons.get(key)
        if found is None and key and self.known_items is not None and key not in self.known_items:
            return WITHHELD_UNKNOWN_ITEM
        return found

    @property
    def item_ids(self) -> frozenset[str]:
        return frozenset(self.reasons)


def excerpt(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _table(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def _loads(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _result(correctness: Any, held: bool) -> str:
    """The card's result classes (``router_card._result``)."""

    if held:
        return "held_for_review"
    if correctness is None:
        return "not_graded"
    value = float(correctness)
    if value >= 0.999:
        return "correct"
    if value <= 0.001:
        return "incorrect"
    return "partial"


# -- the protection predicates ---------------------------------------------------


def protection_issues(vault: Any) -> list[str]:
    """Why the vault's protection metadata cannot be trusted, or ``[]``.

    The source sets name the exam and held-out material. The loader turns a
    source-sets file it cannot read into an issue and no source sets, and a
    file a write has just truncated reads as no source sets at all: either
    way "no exam material", so it makes protection unreadable. So does a
    snapshot the remote runtime saw change while it loaded
    (:data:`SNAPSHOT_UNSETTLED`). A practice item that failed to load is
    handled per item (``Withheld.known_items``)."""

    from learnloop.vault.paths import VaultPaths

    found: list[str] = []
    try:
        source_sets = VaultPaths(Path(vault.root), vault.config).source_sets_path.resolve()
    except Exception:  # noqa: BLE001 - fail closed
        return ["the vault's source sets could not be located"]
    for issue in getattr(vault, "issues", None) or ():
        if issue.code == SNAPSHOT_UNSETTLED:
            found.append(str(issue.message))
        elif issue.path is not None and Path(issue.path).resolve() == source_sets:
            found.append(f"the source sets could not be read ({issue.code})")
    try:
        if source_sets.is_file() and not source_sets.read_bytes().strip():
            found.append("the source sets file is empty (a write in progress)")
    except OSError:
        found.append("the source sets file could not be read")
    return found


def withheld_items(vault: Any, repository: Any) -> Withheld:
    """Every item whose question and answers a remote frontend never shows.

    Exam and held-out material by the one predicate
    (``content.sources.exam_material``: exam members and units, held-out
    units, the unreleased exam pools, and items whose own source is any of
    them, by ``item_exam_status``: the canonical exercise and every
    provenance form, block locators and namespaced span ids included), live
    assessment reservations, items an open cold check or a repair's cold
    retry holds, and diagnostic probes. Any predicate that fails, or
    protection metadata that cannot be trusted (:func:`protection_issues`),
    makes the whole set unavailable (fail closed)."""

    reasons: dict[str, str] = {}
    problems = protection_issues(vault)
    if problems:
        _LOG.warning("learner context: protection metadata not trusted: %s", "; ".join(problems))
        return Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,))
    try:
        from learnloop.content.sources.exam_material import exam_material, held_out_items, item_exam_status

        reserved = frozenset(str(item_id) for item_id in repository.reserved_exam_pool_item_ids())
        for item_id in reserved:
            reasons.setdefault(item_id, WITHHELD_EXAM)
        for item_id in held_out_items(vault, repository):
            reasons.setdefault(str(item_id), WITHHELD_EXAM)
        exam = exam_material(vault, repository)
        for item in vault.practice_items.values():
            if item_exam_status(item, material=exam, reserved=reserved) is not None:
                reasons.setdefault(item.id, WITHHELD_EXAM)
        for row in repository.reserved_assessment_surfaces():
            legacy = row.get("legacy_practice_item_id")
            if legacy:
                reasons.setdefault(str(legacy), WITHHELD_RESERVED)
        for kind in _COLD_TASK_KINDS:
            for task in repository.open_followup_tasks_of_kind(kind):
                if task.get("selected_item_id"):
                    reasons.setdefault(str(task["selected_item_id"]), WITHHELD_COLD)
        with repository.connection() as connection:
            if _table(connection, "remediation_episodes"):
                for row in connection.execute(
                    "SELECT cold_item_id FROM remediation_episodes WHERE cold_item_id IS NOT NULL "
                    "AND state NOT IN ('completed', 'abandoned')"
                ):
                    reasons.setdefault(str(row[0]), WITHHELD_COLD)
            if _table(connection, "probe_presentations"):
                for row in connection.execute(
                    "SELECT DISTINCT practice_item_id FROM probe_presentations"
                ):
                    reasons.setdefault(str(row[0]), WITHHELD_PROBE)
        for item in vault.practice_items.values():
            if item.practice_mode in _PROBE_MODES:
                reasons.setdefault(item.id, WITHHELD_PROBE)
    except Exception:  # noqa: BLE001 - fail closed: nothing shows
        _LOG.warning("learner context: protection predicates not read", exc_info=True)
        return Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,))
    return Withheld(reasons=reasons, known_items=frozenset(str(item_id) for item_id in vault.practice_items))


# -- answer keys (read to filter text, never output) -----------------------------


def _key_identity(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


@dataclass
class KeyBook:
    """Every answer key each item is known to have had: today's YAML and every
    assessment-contract snapshot (an attempt's pinned contract is the key it
    was graded against). Read only to filter free text; never serialized.

    ``changed`` are the items whose known keys differ (edited since a
    snapshot); ``unreadable`` means the snapshots could not be read, so free
    text that could quote a key is withheld."""

    by_item: dict[str, list[Any]] = field(default_factory=dict)
    by_lo: dict[str, list[Any]] = field(default_factory=dict)
    changed: frozenset[str] = frozenset()
    unreadable: bool = False

    def item(self, item_id: str | None) -> list[Any]:
        return list(self.by_item.get(str(item_id or ""), ()))

    def lo(self, lo_id: str | None) -> list[Any]:
        return list(self.by_lo.get(str(lo_id or ""), ()))

    def los(self, lo_ids: Iterable[str]) -> list[Any]:
        return [key for lo_id in dict.fromkeys(lo_ids) for key in self.lo(lo_id)]


def key_book(connection: Any, vault: Any, unknowns: list[str]) -> KeyBook:
    """The :class:`KeyBook` of the vault's items and contract snapshots."""

    by_item: dict[str, dict[str, Any]] = {}
    by_lo: dict[str, dict[str, Any]] = {}

    def add(item_id: Any, lo_id: Any, key: Any) -> None:
        if key in (None, "", {}, []):
            return
        identity = _key_identity(key)
        by_item.setdefault(str(item_id), {})[identity] = key
        if lo_id:
            by_lo.setdefault(str(lo_id), {})[identity] = key

    for item in vault.practice_items.values():
        add(item.id, item.learning_object_id, item.expected_answer)
    unreadable = False
    try:
        if _table(connection, "assessment_contract_versions"):
            for item_id, lo_id, value, kind in connection.execute(
                "SELECT practice_item_id, json_extract(contract_json, '$.learning_object_id'), "
                "json_extract(contract_json, '$.expected_answer'), json_type(contract_json, '$.expected_answer') "
                "FROM assessment_contract_versions"
            ):
                if kind in ("object", "array") and isinstance(value, str):
                    value = json.loads(value)
                item = vault.practice_items.get(str(item_id))
                add(item_id, lo_id or (item.learning_object_id if item is not None else None), value)
    except Exception:  # noqa: BLE001 - fail closed: text that could quote a key is withheld
        _LOG.warning("learner context: contract answer keys not read", exc_info=True)
        unknowns.append("past answer keys could not be read: answers and statements that could quote one are withheld")
        unreadable = True
    return KeyBook(
        by_item={item_id: list(keys.values()) for item_id, keys in by_item.items()},
        by_lo={lo_id: list(keys.values()) for lo_id, keys in by_lo.items()},
        changed=frozenset(item_id for item_id, keys in by_item.items() if len(keys) > 1),
        unreadable=unreadable,
    )


def leaks_key(text: str, expected_answers: Iterable[Any]) -> bool:
    """Whether ``text`` reproduces any of ``expected_answers`` (the tutor's filter)."""

    from learnloop.tutor.tutor_qa import span_leaks_expected

    for expected in expected_answers:
        if expected in (None, "", {}):
            continue
        try:
            if span_leaks_expected(str(text), expected):
                return True
        except Exception:  # noqa: BLE001 - an unreadable key withholds the text
            return True
    return False


def _guarded(text: Any, keys: Iterable[Any], limit: int, *, book: KeyBook | None = None) -> tuple[str | None, str | None]:
    """``(excerpt, note)``: the text, or None with why it is withheld."""

    if not text or not str(text).strip():
        return None, None
    if book is not None and book.unreadable:
        return None, KEYS_UNREADABLE
    if leaks_key(str(text), keys):
        return None, KEY_WITHHELD
    return excerpt(text, limit), None


def _attempt_items(connection: Any, attempt_ids: Iterable[Any]) -> dict[str, str | None]:
    """``{attempt id: its practice item}``; an attempt not on record maps to None."""

    ids = sorted({str(attempt_id) for attempt_id in attempt_ids if attempt_id})
    found: dict[str, str | None] = dict.fromkeys(ids)
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for attempt_id, item_id in connection.execute(
            f"SELECT id, practice_item_id FROM practice_attempts WHERE id IN ({_marks(chunk)})", chunk,
        ):
            found[str(attempt_id)] = None if item_id is None else str(item_id)
    return found


def _withheld_for_attempts(withheld: Withheld, items: Mapping[str, str | None],
                           attempt_ids: Iterable[Any]) -> str | None:
    """Why text drawn from these answers is withheld: the first protected (or
    unrecorded) answer's reason, or None when every answer may be shown."""

    for attempt_id in sorted({str(value) for value in attempt_ids if value}):
        if attempt_id not in items:
            continue
        item_id = items[attempt_id]
        reason = withheld.reason(item_id) if item_id else WITHHELD_UNKNOWN_ITEM
        if reason:
            return reason
    if not withheld.available:
        return WITHHELD_UNREADABLE
    return None


# -- scope -------------------------------------------------------------------------


_WORD = re.compile(r"[a-z0-9]+")


def _forms(word: str) -> tuple[str, ...]:
    """A topic word and its singular (``eigenvalues`` matches ``eigenvalue``)."""

    forms = [word]
    for suffix in ("ies", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            forms.append(word[: -len(suffix)] + ("y" if suffix == "ies" else ""))
            break
    return tuple(forms)


def resolve_scope(vault: Any, *, learning_object_ids: Sequence[str] | None = None,
                  topic: str | None = None) -> dict[str, Any]:
    """The LOs a context is about: named ids, a topic's matches, or every active LO."""

    los = vault.learning_objects
    if learning_object_ids:
        known = [lo for lo in dict.fromkeys(learning_object_ids) if lo in los]
        unknown = [lo for lo in dict.fromkeys(learning_object_ids) if lo not in los]
        return {"learning_object_ids": known, "matched_by": "ids", "unknown_ids": unknown}
    if topic and topic.strip():
        words = [word for word in _WORD.findall(topic.lower()) if len(word) > 2] or _WORD.findall(topic.lower())
        concepts = getattr(vault, "concepts", {}) or {}
        matched: list[tuple[int, str]] = []
        for lo_id, lo in los.items():
            if lo.status != "active":
                continue
            concept = concepts.get(lo.concept)
            haystack = " ".join(filter(None, [
                lo.title, lo.concept.replace("_", " "), getattr(concept, "title", None),
                " ".join(getattr(concept, "aliases", None) or ()),
            ])).lower()
            hits = sum(1 for word in words if any(form in haystack for form in _forms(word)))
            if hits:
                matched.append((-hits, lo_id))
        matched.sort()
        return {"learning_object_ids": [lo for _hits, lo in matched[:40]], "matched_by": "topic",
                "topic": excerpt(topic, 120)}
    active = sorted(lo_id for lo_id, lo in los.items() if lo.status == "active")
    return {"learning_object_ids": active, "matched_by": "all"}


# -- sections ----------------------------------------------------------------------


def _misconceptions(connection: Any, vault: Any, los: set[str], titles: Mapping[str, str],
                    limits: ContextLimits, book: KeyBook,
                    unknowns: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    if not los:
        return registry, candidates
    scope = sorted(los)
    try:
        if _table(connection, "misconceptions"):
            demoted = set()
            if _table(connection, "misconception_disposition_events"):
                demoted = {str(row[0]) for row in connection.execute(
                    "SELECT misconception_id FROM misconception_disposition_events")}
            for row in connection.execute(
                f"SELECT * FROM misconceptions WHERE status IN ('active', 'resolving') "
                f"AND learning_object_id IN ({_marks(scope)}) ORDER BY severity DESC, updated_at DESC, id",
                scope,
            ):
                if str(row["id"]) in demoted:
                    continue
                keys = book.lo(row["learning_object_id"])
                statement, note = _guarded(row["statement"], keys, STATEMENT_LIMIT, book=book)
                correction, correction_note = _guarded(
                    row["correction_statement"] if "correction_statement" in row.keys() else None,
                    keys, STATEMENT_LIMIT, book=book)
                sightings = _loads(row["source_error_event_ids_json"], [])
                registry.append({
                    "misconception_id": row["id"], "learning_object_id": row["learning_object_id"],
                    "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                    "status": row["status"], "statement": statement, "statement_note": note,
                    "correction": correction, "correction_note": correction_note,
                    "severity": round(float(row["severity"] or 0.0), 3),
                    "evidence_count": len(sightings) if isinstance(sightings, list) else 0,
                    "since": row["created_at"], "updated_at": row["updated_at"],
                })
        if _table(connection, "misconception_candidates"):
            for row in connection.execute(
                f"SELECT * FROM misconception_candidates WHERE status = 'candidate' "
                f"AND learning_object_id IN ({_marks(scope)}) ORDER BY occurrence_count DESC, updated_at DESC, id",
                scope,
            ):
                statement, note = _guarded(row["statement"], book.lo(row["learning_object_id"]), STATEMENT_LIMIT,
                                           book=book)
                candidates.append({
                    "candidate_id": row["id"], "learning_object_id": row["learning_object_id"],
                    "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                    "status": "candidate", "statement": statement, "statement_note": note,
                    "evidence_count": int(row["occurrence_count"] or 0),
                    "note": "held until it recurs; not yet a recorded misconception",
                    "since": row["created_at"], "updated_at": row["updated_at"],
                })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: misconceptions not read", exc_info=True)
        unknowns.append("misconceptions could not be read")
    return registry[: limits.misconceptions], candidates[: limits.candidates]


def _hypotheses(connection: Any, vault: Any, los: set[str], titles: Mapping[str, str],
                limits: ContextLimits, withheld: Withheld, book: KeyBook,
                unknowns: list[str]) -> list[dict[str, Any]]:
    """Open hypotheses: the diagnosed causes, then the unresolved causes (each
    read on its own, so an LO with unresolved causes and no named hypothesis
    still shows them)."""

    if not los:
        return []
    return _diagnosed_causes(connection, los, titles, limits, withheld, book, unknowns) + \
        _unresolved_causes(connection, los, titles, limits, unknowns)


def _diagnosed_causes(connection: Any, los: set[str], titles: Mapping[str, str], limits: ContextLimits,
                      withheld: Withheld, book: KeyBook, unknowns: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        if not _table(connection, "causal_hypotheses"):
            return entries
        from learnloop.db.stores.daily_plans import open_learner_state_hypotheses

        rows = open_learner_state_hypotheses(connection, los)[: limits.hypotheses]
        if not rows:
            return entries
        ids = [row["id"] for row in rows]
        heads = {str(row["id"]): dict(row) for row in connection.execute(
            f"SELECT id, episode_key, version, repair_class_id FROM causal_hypotheses WHERE id IN ({_marks(ids)})", ids)}
        episode_keys = sorted({str(head["episode_key"]) for head in heads.values()})
        versions: dict[str, list[dict[str, Any]]] = {}
        for row in connection.execute(
            f"SELECT episode_key, attempt_id, status FROM causal_hypotheses WHERE episode_key IN ({_marks(episode_keys)})",
            episode_keys,
        ):
            versions.setdefault(str(row["episode_key"]), []).append(dict(row))
        attempt_ids = sorted({str(v["attempt_id"]) for rows_ in versions.values() for v in rows_ if v["attempt_id"]})
        attempt_items = _attempt_items(connection, [*attempt_ids, *(row["attempt_id"] for row in rows)])
        feedback: dict[str, list[str]] = {}
        if attempt_ids and _table(connection, "diagnosis_feedback"):
            for row in connection.execute(
                f"SELECT attempt_id, response FROM diagnosis_feedback WHERE attempt_id IN ({_marks(attempt_ids)})",
                attempt_ids,
            ):
                feedback.setdefault(str(row["attempt_id"]), []).append(str(row["response"]))
        groups: dict[str, int] = {}
        if _table(connection, "hypothesis_recurrence_groups"):
            for row in connection.execute(
                f"SELECT episode_key, class_count FROM hypothesis_recurrence_groups "
                f"WHERE episode_key IN ({_marks(episode_keys)})", episode_keys,
            ):
                groups[str(row["episode_key"])] = int(row["class_count"])
        verifications: dict[str, list[int]] = {}
        if _table(connection, "causal_cold_verifications"):
            for row in connection.execute("SELECT hypothesis_ids_json, success FROM causal_cold_verifications"):
                for hypothesis_id in _loads(row["hypothesis_ids_json"], []) or []:
                    verifications.setdefault(str(hypothesis_id), []).append(int(row["success"]))
        repair_refs = set(ids) | set(episode_keys) | {
            str(row["promoted_misconception_id"]) for row in rows if row.get("promoted_misconception_id")}
        repairs: dict[str, list[dict[str, Any]]] = {}
        if repair_refs and _table(connection, "remediation_episodes"):
            refs = sorted(repair_refs)
            for row in connection.execute(
                f"SELECT id, case_kind, case_ref, state, created_at, completed_at FROM remediation_episodes "
                f"WHERE case_ref IN ({_marks(refs)}) ORDER BY created_at", refs,
            ):
                repairs.setdefault(str(row["case_ref"]), []).append({
                    "episode_id": row["id"], "state": row["state"], "started_at": row["created_at"],
                    "completed_at": row["completed_at"]})
        for row in rows:
            head = heads.get(str(row["id"])) or {}
            episode = str(head.get("episode_key") or "")
            episode_attempts = {str(v["attempt_id"]) for v in versions.get(episode, []) if v["attempt_id"]}
            responses = [response for attempt in episode_attempts for response in feedback.get(attempt, [])]
            tried = (repairs.get(str(row["id"]), []) + repairs.get(episode, [])
                     + repairs.get(str(row.get("promoted_misconception_id") or ""), []))
            outcomes = verifications.get(str(row["id"]), [])
            # The statement is drawn from every answer of its episode: one
            # protected (or unreadable) answer withholds it.
            reason = _withheld_for_attempts(withheld, attempt_items, [*episode_attempts, row.get("attempt_id")])
            if reason:
                statement, note = None, f"withheld: {reason}"
            else:
                statement, note = _guarded(row["statement"], book.lo(row["learning_object_id"]), STATEMENT_LIMIT,
                                           book=book)
            entries.append({
                "kind": "diagnosed_cause", "learning_object_id": row["learning_object_id"],
                "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                "status": row["status"], "since": row["created_at"], "statement": statement,
                "statement_note": note, "hypothesis_id": row["id"], "attempt_id": row["attempt_id"],
                "error_event_id": row["error_event_id"],
                "promoted_misconception_id": row.get("promoted_misconception_id"),
                "label": "a hypothesis, not a finding" if row["status"] == "candidate" else "validated by evidence",
                "evidence_for": {
                    "answers_in_episode": len(episode_attempts),
                    "recurrence_class_count": groups.get(episode, 0),
                    "learner_confirmed": sum(1 for r in responses if r in ("believed_candidate", "partly")),
                    "cold_checks_failed": sum(1 for success in outcomes if not success),
                },
                "evidence_against": {
                    "learner_disputed": sum(1 for r in responses if r in ("diagnosis_wrong", "slipped",
                                                                           "not_same_mistake")),
                    "cold_checks_passed": sum(1 for success in outcomes if success),
                },
                "repairs_tried": tried,
            })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: open hypotheses not read", exc_info=True)
        unknowns.append("open hypotheses could not be read")
    return entries[: limits.hypotheses]


def _unresolved_causes(connection: Any, los: set[str], titles: Mapping[str, str], limits: ContextLimits,
                       unknowns: list[str]) -> list[dict[str, Any]]:
    """Answers whose cause is not settled, per LO (a count; no answer text)."""

    entries: list[dict[str, Any]] = []
    try:
        if not _table(connection, "unresolved_cause_factors"):
            return entries
        scope = sorted(los)
        for row in connection.execute(
            f"""SELECT a.learning_object_id, COUNT(*) AS n, MIN(f.created_at) AS since
                  FROM unresolved_cause_factors f JOIN practice_attempts a ON a.id = f.attempt_id
                 WHERE f.status = 'open' AND a.learning_object_id IN ({_marks(scope)})
                 GROUP BY a.learning_object_id ORDER BY a.learning_object_id""",
            scope,
        ):
            entries.append({
                "kind": "unresolved_cause", "learning_object_id": row["learning_object_id"],
                "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                "status": "open", "since": row["since"],
                "statement": f"{row['n']} answer(s) whose cause is not settled",
            })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: unresolved causes not read", exc_info=True)
        unknowns.append("unresolved causes could not be read")
    return entries[: limits.hypotheses]


def _recurrence_groups(connection: Any, los: set[str], titles: Mapping[str, str], limits: ContextLimits,
                       withheld: Withheld, book: KeyBook, unknowns: list[str]) -> list[dict[str, Any]]:
    """Groups touching the scope's LOs. An empty scope has none (a topic or
    ids that matched nothing is not a whole-learner request: that scope is
    every active LO). A group's statement is its root's; it is withheld when
    any answer behind any member is protected or unreadable."""

    groups: list[dict[str, Any]] = []
    if not los:
        return groups
    try:
        if not (_table(connection, "hypothesis_recurrence_groups") and _table(connection, "causal_hypotheses")):
            return groups
        members: dict[str, list[dict[str, Any]]] = {}
        for row in connection.execute(
            """SELECT g.group_key, g.episode_key, g.root_episode_key, g.class_count, g.joined_by,
                      h.learning_object_id, h.statement
                 FROM hypothesis_recurrence_groups g
                 JOIN causal_hypotheses h ON h.episode_key = g.episode_key
                  AND h.version = (SELECT MAX(v.version) FROM causal_hypotheses v WHERE v.episode_key = g.episode_key)
                ORDER BY g.group_key, g.episode_key"""
        ):
            members.setdefault(str(row["group_key"]), []).append(dict(row))
        selected = {key: rows for key, rows in members.items()
                    if {str(row["learning_object_id"]) for row in rows} & los}
        episodes = sorted({str(row["episode_key"]) for rows in selected.values() for row in rows})
        attempts: dict[str, set[str]] = {}
        for start in range(0, len(episodes), 500):
            chunk = episodes[start:start + 500]
            for episode, attempt_id in connection.execute(
                f"SELECT episode_key, attempt_id FROM causal_hypotheses WHERE episode_key IN ({_marks(chunk)})", chunk,
            ):
                if attempt_id:
                    attempts.setdefault(str(episode), set()).add(str(attempt_id))
        attempt_items = _attempt_items(connection, [a for values in attempts.values() for a in values])
        for group_key, rows in selected.items():
            lo_ids = sorted({str(row["learning_object_id"]) for row in rows})
            root = next((row for row in rows if row["episode_key"] == row["root_episode_key"]), rows[0])
            behind = [attempt for row in rows for attempt in attempts.get(str(row["episode_key"]), ())]
            reason = _withheld_for_attempts(withheld, attempt_items, behind)
            if reason:
                statement, note = None, f"withheld: {reason}"
            else:
                statement, note = _guarded(root["statement"], book.los(lo_ids), STATEMENT_LIMIT, book=book)
            groups.append({
                "group_key": group_key, "statement": statement, "statement_note": note,
                "episodes": len(rows), "class_count": max(int(row["class_count"]) for row in rows),
                "joined_by": sorted({str(row["joined_by"]) for row in rows}),
                "learning_object_ids": lo_ids, "topics": [titles.get(lo, lo) for lo in lo_ids],
                "label": "the same cause seen more than once",
            })
        groups.sort(key=lambda group: (-group["class_count"], group["group_key"]))
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: recurrence groups not read", exc_info=True)
        unknowns.append("recurrence groups could not be read")
    return groups[: limits.groups]


def _pinned_stems(connection: Any, attempts: Sequence[Mapping[str, Any]], unknowns: list[str]) -> dict[str, str | None]:
    """The question each attempt answered: its pinned assessment contract's
    prompt (only the prompt is read here, never the key or rubric). An attempt
    with no contract, or several, is not pinned (router R2a review F6). The
    keys of every contract are in the :class:`KeyBook`, for filtering only.

    ``{attempt id: prompt or None}`` for the pinned attempts."""

    items = {str(row["id"]): row.get("practice_item_id") for row in attempts}
    if not items:
        return {}
    try:
        if not _table(connection, "assessment_contract_versions"):
            return {}
        contracts: dict[str, set[Any]] = {}
        for attempt_id, contract_id in connection.execute(
            f"SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
            f"WHERE superseded_at IS NULL AND attempt_id IN ({_marks(list(items))})",
            list(items),
        ):
            contracts.setdefault(str(attempt_id), set()).add(contract_id)
        single = {attempt: next(iter(ids)) for attempt, ids in contracts.items() if len(ids) == 1 and None not in ids}
        if not single:
            return {}
        versions = sorted({str(value) for value in single.values()})
        prompts = {
            str(row[0]): (row[1], row[2])
            for row in connection.execute(
                f"SELECT id, practice_item_id, json_extract(contract_json, '$.prompt') "
                f"FROM assessment_contract_versions WHERE id IN ({_marks(versions)})",
                versions,
            )
        }
    except Exception:  # noqa: BLE001 - named as unknown; no question shows
        _LOG.warning("learner context: pinned questions not read", exc_info=True)
        unknowns.append("the questions past work answered could not be read: none is shown")
        return {}
    stems: dict[str, str | None] = {}
    for attempt_id, version_id in single.items():
        item_id, prompt = prompts.get(str(version_id), (None, None))
        if item_id is not None and item_id == items.get(attempt_id):
            stems[attempt_id] = prompt if isinstance(prompt, str) and prompt.strip() else None
    return stems


def _traces(connection: Any, repository: Any, los: set[str], titles: Mapping[str, str], limits: ContextLimits,
            withheld: Withheld, book: KeyBook, unknowns: list[str], now_iso: str) -> list[dict[str, Any]]:
    from learnloop.held_grades import held_for_review_attempts

    if not los:
        return []
    scope = sorted(los)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")}

    def column(name: str, default: str = "NULL") -> str:
        return name if name in columns else f"{default} AS {name}"

    rows = [dict(row) for row in connection.execute(
        f"SELECT id, practice_item_id, learning_object_id, practice_mode, attempt_type, correctness, hints_used, "
        f"primed, learner_answer_md, created_at, probe_presentation_id, {column('reference_status')}, "
        f"{column('entry_surface')}, {column('evidence_origin')}, {column('declared_stuck', '0')}, "
        f"{column('declared_dont_know', '0')} FROM practice_attempts "
        f"WHERE learning_object_id IN ({_marks(scope)}) AND created_at <= ? ORDER BY created_at DESC, id DESC LIMIT ?",
        (*scope, now_iso, int(limits.traces)),
    )]
    if not rows:
        return []
    ids = [row["id"] for row in rows]
    held = held_for_review_attempts(connection, ids)
    pinned = _pinned_stems(connection, rows, unknowns)
    blind = set()
    if _table(connection, "blind_grade_records"):
        blind = {str(row[0]) for row in connection.execute(
            f"SELECT DISTINCT attempt_id FROM blind_grade_records WHERE attempt_id IN ({_marks(ids)})", ids)}
    cold: dict[str, Any] = {}
    if _table(connection, "coldness_receipts"):
        for row in connection.execute(
            f"SELECT cold_attempt_id, lane, derived_json FROM coldness_receipts WHERE stage = 'final' "
            f"AND cold_attempt_id IN ({_marks(ids)}) ORDER BY created_at", ids,
        ):
            derived = _loads(row["derived_json"], {}) or {}
            cold[str(row["cold_attempt_id"])] = {"lane": row["lane"],
                                                 "qualified": derived.get("qualifies_as_cold_retrieval")}
    hypotheses: dict[str, list[str]] = {}
    if _table(connection, "causal_hypotheses"):
        for row in connection.execute(
            f"SELECT attempt_id, statement FROM causal_hypotheses WHERE cause_scope = 'learner_state' "
            f"AND status IN ('candidate', 'validated') AND attempt_id IN ({_marks(ids)}) ORDER BY created_at", ids,
        ):
            hypotheses.setdefault(str(row["attempt_id"]), []).append(str(row["statement"]))
    reveals: dict[str, int] = {}
    if _table(connection, "reveal_events"):
        for row in rows:
            found = connection.execute(
                "SELECT COUNT(*) FROM reveal_events WHERE practice_item_id = ? AND created_at <= ?",
                (row["practice_item_id"], row["created_at"]),
            ).fetchone()
            reveals[row["id"]] = int(found[0])
    traces: list[dict[str, Any]] = []
    for row in rows:
        attempt_id = str(row["id"])
        item_id = row["practice_item_id"]
        reason = withheld.reason(item_id)
        if reason is None and row.get("attempt_type") in _EXAM_ATTEMPT_TYPES:
            reason = WITHHELD_EXAM
        if reason is None and (row.get("attempt_type") == "diagnostic_probe" or row.get("probe_presentation_id")):
            reason = WITHHELD_PROBE
        # Every key the item is known to have had, the pinned one among them.
        # Without a pin, an item whose key has changed leaves the key this
        # answer was graded against unknown: its text is withheld (fail closed).
        keys = book.item(item_id)
        revision_known = attempt_id in pinned or str(item_id or "") not in book.changed
        answer = answer_note = None
        if reason is None:
            if revision_known:
                answer, answer_note = _guarded(row.get("learner_answer_md"), keys, EXCERPT_LIMIT, book=book)
            elif str(row.get("learner_answer_md") or "").strip():
                answer_note = REVISION_UNKNOWN
        stem = None if reason else pinned.get(attempt_id)
        diagnosis = _diagnosis(repository, attempt_id, keys, book, hidden=reason is not None,
                               revision_known=revision_known, statements=hypotheses.get(attempt_id, []))
        status = row.get("reference_status")
        traces.append({
            "attempt_id": attempt_id, "at": row["created_at"], "learning_object_id": row["learning_object_id"],
            "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
            "kind": row.get("practice_mode"), "attempt_type": row.get("attempt_type"),
            "result": _result(row["correctness"], attempt_id in held),
            "graded_by": "blind_grader" if attempt_id in blind else "recorded",
            "hints_used": int(row.get("hints_used") or 0), "assisted": bool(row.get("primed")),
            "revealed_before": reveals.get(attempt_id, 0) > 0,
            "declared_stuck": bool(row.get("declared_stuck")), "said_dont_know": bool(row.get("declared_dont_know")),
            "cold_check": cold.get(attempt_id),
            "entry_surface": row.get("entry_surface"), "evidence_origin": row.get("evidence_origin"),
            "key_status": status if status in ("verified", "unverified") else None,
            "withheld": reason,
            "stem": excerpt(stem, STEM_LIMIT) if stem else None,
            "stem_note": None if reason or stem else "question revision not recorded",
            "answer": answer, "answer_note": answer_note,
            "diagnosis": diagnosis,
        })
    return traces


def _diagnosis(repository: Any, attempt_id: str, keys: Sequence[Any], book: KeyBook, *, hidden: bool,
               revision_known: bool, statements: Sequence[str]) -> dict[str, Any]:
    from learnloop.diagnosis.split.card import plain_summary
    from learnloop.diagnosis.split.jobs import DONE, diagnosis_status

    try:
        status = diagnosis_status(repository, attempt_id)
    except Exception:  # noqa: BLE001 - named on the trace
        return {"status": "unknown"}
    entry: dict[str, Any] = {"status": status.get("status")}
    if hidden:
        return entry
    summary = None
    if status.get("status") == DONE and status.get("diagnosis_id"):
        diagnosis = repository.attempt_diagnosis(str(status["diagnosis_id"])) or {}
        analysis = str((diagnosis.get("proposal") or {}).get("analysis_md") or "")
        if analysis:
            if revision_known:
                summary, note = _guarded(plain_summary(repository, analysis), keys, STATEMENT_LIMIT, book=book)
            else:
                note = REVISION_UNKNOWN
            if note:
                entry["summary_note"] = note
    entry["summary"] = summary
    if not revision_known:
        entry["hypotheses"] = []
        if statements:
            entry["hypotheses_note"] = REVISION_UNKNOWN
        return entry
    guarded = [_guarded(text, keys, STATEMENT_LIMIT, book=book) for text in statements]
    entry["hypotheses"] = [text for text, _note in guarded if text]
    notes = [note for _text, note in guarded if note]
    if notes:
        entry["hypotheses_note"] = notes[0]
    return entry


def _gap_target(connection: Any, kind: str | None, target_id: str | None, titles: Mapping[str, str],
                book: KeyBook) -> str | None:
    """What a gap was matched to, in words: a topic, a recorded misconception or a candidate."""

    if not kind or not target_id:
        return None
    if kind == "learning_object":
        return titles.get(target_id, target_id)
    table = {"durable": "misconceptions", "candidate": "misconception_candidates"}.get(kind)
    if table is None or not _table(connection, table):
        return None
    row = connection.execute(f"SELECT learning_object_id, statement FROM {table} WHERE id = ?", (target_id,)).fetchone()
    if row is None:
        return None
    statement, _note = _guarded(row["statement"], book.lo(row["learning_object_id"]), STATEMENT_LIMIT, book=book)
    return statement


def _gaps(connection: Any, los: set[str], titles: Mapping[str, str], limits: ContextLimits,
          withheld: Withheld, book: KeyBook, unknowns: list[str]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if not los:
        return gaps
    try:
        if not _table(connection, "learner_text_gaps"):
            return gaps
        reversed_ids: set[str] = set()
        if _table(connection, "learner_text_gap_reversals"):
            reversed_ids = {str(row[0]) for row in connection.execute("SELECT gap_id FROM learner_text_gap_reversals")}
        scope = sorted(los)
        for row in connection.execute(
            f"""SELECT id, source_kind, practice_item_id, anchor_learning_object_id, target_kind, target_id, kind,
                       action, learner_text, created_at
                  FROM learner_text_gaps
                 WHERE kind IN ('prerequisite', 'misconception')
                   AND (anchor_learning_object_id IN ({_marks(scope)})
                        OR (target_kind = 'learning_object' AND target_id IN ({_marks(scope)})))
                 ORDER BY created_at DESC, id DESC""",
            (*scope, *scope),
        ):
            if str(row["id"]) in reversed_ids:
                continue
            lo = row["target_id"] if row["target_kind"] == "learning_object" and row["target_id"] in los \
                else row["anchor_learning_object_id"]
            reason = withheld.reason(row["practice_item_id"]) if row["practice_item_id"] else (
                None if withheld.available else WITHHELD_UNREADABLE)
            text, note = (None, f"withheld: {reason}") if reason else _guarded(
                row["learner_text"], book.item(row["practice_item_id"]), STATEMENT_LIMIT, book=book)
            target = _gap_target(connection, row["target_kind"], row["target_id"], titles, book)
            gaps.append({
                "gap_id": row["id"], "kind": row["kind"], "action": row["action"],
                "learning_object_id": lo, "topic": titles.get(lo, lo), "target": target,
                "learner_text": text, "learner_text_note": note, "source": row["source_kind"],
                "since": row["created_at"],
                "label": "named from the learner's own words; reversible with 'not this'",
            })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: learner-text gaps not read", exc_info=True)
        unknowns.append("open learner-text gaps could not be read")
    return gaps[: limits.gaps]


def retention_risks(vault: Any, repository: Any, los: Iterable[str], *, now: datetime, limit: int = 15,
                    unknowns: list[str] | None = None) -> list[dict[str, Any]]:
    """Topics whose modelled recall now is below :data:`RETENTION_TARGET`, or due now.

    FSRS retrievability from each item's stored memory state: a model
    estimate, not a test. Lowest recall first."""

    from learnloop.params.fitted_params import resolve_fsrs_weights
    from learnloop.scheduling.fsrs import forgetting_curve

    los = set(los)
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    unknowns = unknowns if unknowns is not None else []
    try:
        weights = resolve_fsrs_weights(repository)
        states = repository.practice_item_states()
    except Exception:  # noqa: BLE001 - named as unknown
        unknowns.append("retention could not be read")
        return []
    by_lo: dict[str, dict[str, Any]] = {}
    for item_id, state in states.items():
        item = vault.practice_items.get(item_id)
        if item is None or item.status != "active" or not getattr(state, "active", True):
            continue
        if item.learning_object_id not in los:
            continue
        stability = getattr(state, "stability", None)
        last = parse_utc(getattr(state, "last_attempt_at", None))
        if not stability or last is None:
            continue
        elapsed = max((now - last).total_seconds() / 86400.0, 0.0)
        recall = float(forgetting_curve(float(stability), elapsed, weights))
        entry = by_lo.setdefault(item.learning_object_id, {"recalls": [], "due_now": 0, "next_due_at": None})
        entry["recalls"].append(recall)
        due = getattr(state, "due_at", None)
        due_at = parse_utc(due)
        if due_at is not None and due_at <= now:
            entry["due_now"] += 1
        if due and (entry["next_due_at"] is None or str(due) < entry["next_due_at"]):
            entry["next_due_at"] = str(due)
    risks = []
    for lo_id, entry in by_lo.items():
        below = sum(1 for value in entry["recalls"] if value < RETENTION_TARGET)
        if not below and not entry["due_now"]:
            continue
        risks.append({
            "learning_object_id": lo_id, "topic": titles.get(lo_id, lo_id),
            "recall_now": round(sum(entry["recalls"]) / len(entry["recalls"]), 3),
            "items_below_target": below, "items_due_now": entry["due_now"], "items_tracked": len(entry["recalls"]),
            "next_due_at": entry["next_due_at"],
        })
    risks.sort(key=lambda risk: (risk["recall_now"], risk["learning_object_id"]))
    return risks[: max(int(limit), 0)]


# -- the read model ----------------------------------------------------------------


def learning_context(
    vault: Any,
    repository: Any,
    *,
    learning_object_ids: Sequence[str] | None = None,
    topic: str | None = None,
    now: datetime | None = None,
    limits: ContextLimits | None = None,
    withheld: Withheld | None = None,
) -> dict[str, Any]:
    """The shared latent-state read model for one scope. Read-only."""

    limits = limits or ContextLimits()
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    now_iso = moment.strftime("%Y-%m-%dT%H:%M:%SZ") if now is not None else utc_now_iso()
    scope = resolve_scope(vault, learning_object_ids=learning_object_ids, topic=topic)
    los = set(scope["learning_object_ids"])
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    unknowns: list[str] = []
    withheld = withheld if withheld is not None else withheld_items(vault, repository)
    unknowns.extend(withheld.unknowns)
    with repository.connection() as connection:
        book = key_book(connection, vault, unknowns)
        misconceptions, candidates = _misconceptions(connection, vault, los, titles, limits, book, unknowns)
        hypotheses = _hypotheses(connection, vault, los, titles, limits, withheld, book, unknowns)
        groups = _recurrence_groups(connection, los, titles, limits, withheld, book, unknowns)
        try:
            traces = _traces(connection, repository, los, titles, limits, withheld, book, unknowns, now_iso)
        except Exception:  # noqa: BLE001 - named as unknown
            _LOG.warning("learner context: answer traces not read", exc_info=True)
            unknowns.append("recent answer traces could not be read")
            traces = []
        gaps = _gaps(connection, los, titles, limits, withheld, book, unknowns)
    risks = retention_risks(vault, repository, los, now=moment, limit=limits.risks, unknowns=unknowns)
    if scope["matched_by"] == "topic" and not los:
        unknowns.append("no topic in the vault matched; LearnLoop has no record about it")
    if scope["matched_by"] == "ids" and not los:
        unknowns.append("none of the named learning objects is in this vault; LearnLoop has no record about them")
    return {
        "context_version": CONTEXT_VERSION,
        "as_of": now_iso,
        "scope": {**scope, "learning_object_count": len(los)},
        "misconceptions": misconceptions,
        "misconception_candidates": candidates,
        "open_hypotheses": hypotheses,
        "recurrence_groups": groups,
        "recent_answer_traces": traces,
        "open_learner_text_gaps": gaps,
        "retention_risks": risks,
        "unknowns": unknowns,
        "labels": {
            "evidence": "only a submitted, blind-graded answer is evidence; everything else here is context",
            "hypotheses": "hypotheses are revisable; the learner can say 'not this'",
            "held_for_review": "a held grade has no score yet",
            "recall_now": "a model estimate, not a test",
        },
    }


__all__ = [
    "CONTEXT_VERSION",
    "ContextLimits",
    "KEY_WITHHELD",
    "KeyBook",
    "PROTECTION_UNKNOWN",
    "RETENTION_TARGET",
    "SNAPSHOT_UNSETTLED",
    "WITHHELD_UNKNOWN_ITEM",
    "WITHHELD_UNREADABLE",
    "Withheld",
    "excerpt",
    "key_book",
    "leaks_key",
    "learning_context",
    "protection_issues",
    "resolve_scope",
    "retention_risks",
    "withheld_items",
]
