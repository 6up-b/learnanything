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
  output;
* **answer-derived text has one renderer** (:meth:`AnswerTextGuard.render`,
  F4 round 3): every text drawn from an answer or an error event, directly or
  through a diagnosis, a hypothesis, a recurrence group, a recorded
  misconception (statement and correction), a candidate, or a learner-text
  gap (its words and its target), is released only by it, as a
  :class:`GuardedText`, and :data:`ANSWER_DERIVED_FIELDS` names every such
  field of the output. It follows the text's provenance (:class:`Origin`: the
  answers behind it, through error events, hypothesis episodes, promotions,
  error hunts, gaps and a diagnosis's context receipt) and releases it only
  when every answer behind it
  passes the answers' own protection check (:meth:`AnswerTextGuard.attempt_reason`)
  and was graded against exactly one pinned assessment contract on its own
  item (the affirmative record of the question revision: an older answer may
  restate a key nothing records any more, and the absence of a recorded
  change does not establish the revision), and the text reproduces no key its
  items or topics are known to have had (today's YAML, every
  assessment-contract and practice-item snapshot: :class:`KeyBook`;
  ``tutor_qa.span_leaks_expected``, the tutor's own filter). A link it cannot
  follow (an id list with any member that is not an id, F4 round 4), or text
  about an item with no graded answer behind it, is withheld too. A withheld
  text keeps its entry, counts and status, and says why;
* **provenance is followed transitively** (:meth:`AnswerTextGuard.closure`,
  F4 round 4), cycles handled: a belief drawn from an answer's error events
  follows that answer's grading, so every completed live diagnosis of it (the
  overlay lays a diagnosis's causes on the answer's events) and its joint
  grader's history, and each diagnosis follows everything its context receipt
  says it was shown; a gap that read a diagnosis follows it;
* **topic names and ids have one renderer too** (:meth:`AnswerTextGuard.topic`,
  :meth:`AnswerTextGuard.lo_ref`, F4 round 4): the learner-text pipeline
  drafts a missing prerequisite's titles from the learner's text and derives
  its ids from them, so a generated topic's name is rendered like any other
  answer-derived text; while it is withheld the entry shows a fixed label and
  an opaque alias (accepted back as a named id), and a topic search does not
  match its words;
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

import hashlib
import json
import logging
import re
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
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
REVISION_UNKNOWN = "withheld: the question revision this answer was graded against is not recorded"
REVISION_UNKNOWN_BEHIND = "withheld: the question revision an answer behind it was graded against is not recorded"
REVISION_UNKNOWN_ASKED = ("withheld: it was written about a question with no graded answer behind it, so the "
                          "question revision is not recorded")
PROVENANCE_MISSING = ("withheld: a record it was drawn from (an answer, an error event or a diagnosis's context) "
                      "is not on record")
PROVENANCE_UNKNOWN = "withheld: what it was drawn from is not recorded"
ANSWER_UNRECORDED = "an answer it was drawn from is not on record"
PINS_UNREADABLE = ("the question revisions past answers were graded against could not be read: no question, answer "
                   "or statement drawn from one is shown")
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
    """Every answer key each item is known to have had: today's YAML, every
    assessment-contract snapshot (an attempt's pinned contract is the key it
    was graded against) and every practice-item snapshot the scheduler kept.
    Read only to filter free text; never serialized. It is a filter, not
    evidence of a revision: a key nothing records is not in it, which is why
    an answer also needs its pinned contract (:func:`_pins`).

    ``unreadable`` means the snapshots could not be read, so free text that
    could quote a key is withheld."""

    by_item: dict[str, list[Any]] = field(default_factory=dict)
    by_lo: dict[str, list[Any]] = field(default_factory=dict)
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
        if _table(connection, "practice_item_snapshots"):
            for item_id, lo_id, value, kind in connection.execute(
                "SELECT practice_item_id, json_extract(item_json, '$.learning_object_id'), "
                "json_extract(item_json, '$.expected_answer'), json_type(item_json, '$.expected_answer') "
                "FROM practice_item_snapshots"
            ):
                if kind in ("object", "array") and isinstance(value, str):
                    value = json.loads(value)
                add(item_id, lo_id, value)
    except Exception:  # noqa: BLE001 - fail closed: text that could quote a key is withheld
        _LOG.warning("learner context: contract answer keys not read", exc_info=True)
        unknowns.append("past answer keys could not be read: answers and statements that could quote one are withheld")
        unreadable = True
    return KeyBook(
        by_item={item_id: list(keys.values()) for item_id, keys in by_item.items()},
        by_lo={lo_id: list(keys.values()) for lo_id, keys in by_lo.items()},
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


def _pins(connection: Any, items: Mapping[str, Any], unknowns: list[str]) -> dict[str, Any]:
    """``{attempt id: its pinned contract's prompt or None}`` for the attempts
    (``{attempt id: practice item}``) graded against exactly one assessment
    contract of their own item: the only affirmative record of the question
    revision an answer was graded against (router R2a review F6). Only the
    prompt is read, never the key or rubric. Unreadable: none is pinned."""

    ids = [str(attempt_id) for attempt_id in items if attempt_id]
    if not ids:
        return {}
    try:
        if not _table(connection, "assessment_contract_versions") or not _table(connection, "grading_evidence"):
            return {}
        contracts: dict[str, set[Any]] = {}
        for start in range(0, len(ids), 500):
            chunk = ids[start:start + 500]
            for attempt_id, contract_id in connection.execute(
                f"SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
                f"WHERE superseded_at IS NULL AND attempt_id IN ({_marks(chunk)})", chunk,
            ):
                contracts.setdefault(str(attempt_id), set()).add(contract_id)
        single = {attempt: next(iter(found)) for attempt, found in contracts.items()
                  if len(found) == 1 and None not in found}
        versions = sorted({str(value) for value in single.values()})
        prompts: dict[str, tuple[Any, Any]] = {}
        for start in range(0, len(versions), 500):
            chunk = versions[start:start + 500]
            for row in connection.execute(
                f"SELECT id, practice_item_id, json_extract(contract_json, '$.prompt') "
                f"FROM assessment_contract_versions WHERE id IN ({_marks(chunk)})", chunk,
            ):
                prompts[str(row[0])] = (row[1], row[2])
    except Exception:  # noqa: BLE001 - named as unknown; nothing drawn from an answer shows
        _LOG.warning("learner context: pinned contracts not read", exc_info=True)
        if PINS_UNREADABLE not in unknowns:
            unknowns.append(PINS_UNREADABLE)
        return {}
    pinned: dict[str, Any] = {}
    for attempt_id, version_id in single.items():
        item_id, prompt = prompts.get(str(version_id), (None, None))
        if item_id is not None and str(item_id) == str(items.get(attempt_id) or ""):
            pinned[attempt_id] = prompt if isinstance(prompt, str) and prompt.strip() else None
    return pinned


# -- answer-derived text: the one guarded renderer (F4 rounds 3 and 4) ---------------


_RELEASE = object()
#: Gap sources whose words are an answer itself (``learner_text_gaps.source_kind``).
_ANSWER_SOURCES = frozenset({"diagnosis", "stuck_answer"})
#: A record id as the diagnoser writes it (``diagnosis.split.card``'s ULID form).
_RECORD_ID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_CHUNK = 500
#: The id the learner-text pipeline gives a prerequisite it creates
#: (``text_gaps.actions.creation_ids``: ``lo_ltg_<slug of its title>_<hash>``).
_GENERATED_LO_PREFIX = "lo_ltg_"
#: What stands for a generated topic's id while its name is withheld (F4 round 4).
LO_ALIAS_PREFIX = "lo_withheld_"
#: What stands for a generated topic's name while it is withheld; the note
#: saying why follows it ("..., its name withheld: <why>").
TOPIC_WITHHELD = "a topic named from the learner's own words, its name"
TITLE_LIMIT = 200
_ID_LIMIT = 512


class GuardedText(str):
    """Text :meth:`AnswerTextGuard.render` released, and only it: the
    constructor takes a module-private token. Answer-derived text, and every
    topic name and topic id (F4 round 4), is one of these in the output; the
    output-schema test checks that every field in :data:`ANSWER_DERIVED_FIELDS`,
    :data:`TOPIC_FIELDS` and :data:`TOPIC_ID_FIELDS` holds one (or nothing, or
    a withheld name's fixed label or alias). Copies and pickles are plain
    ``str``."""

    __slots__ = ()

    def __new__(cls, value: str, token: object) -> GuardedText:
        if token is not _RELEASE:
            raise TypeError("answer-derived text is released only by AnswerTextGuard.render")
        return super().__new__(cls, value)

    def __reduce__(self) -> tuple[Any, ...]:
        return (str, (str(self),))


@dataclass(frozen=True)
class Origin:
    """What a piece of answer-derived text was drawn from: the closure of its
    provenance (:meth:`AnswerTextGuard.closure`).

    ``attempts``: the answers behind it (directly, or through an error event,
    the grading and every diagnosis of an answer, a hypothesis episode, a
    promotion, an error hunt, a gap, a diagnosis's context, a generated
    topic's drafting); ``items``: items it is about, each needing a pinned
    answer of its own behind it; ``los``: topics whose keys also filter it (a
    statement's, or the topic of words tied to no item); ``missing``: a link
    that could not be followed (an error event, answer, gap or diagnosis not
    on record, an id list that cannot be read, a diagnosis with no context
    receipt); ``unattached``: text about no item and no answer (a question
    asked in the Reader or the library), to which no revision applies;
    ``direct``: the text is the answer itself or its own diagnosis (the note
    then names "this answer")."""

    attempts: frozenset[str] = frozenset()
    items: frozenset[str] = frozenset()
    los: frozenset[str] = frozenset()
    missing: bool = False
    unattached: bool = False
    direct: bool = False

    def __or__(self, other: Origin) -> Origin:
        return Origin(self.attempts | other.attempts, self.items | other.items, self.los | other.los,
                      self.missing or other.missing, self.unattached or other.unattached, False)

    def about(self, *los: Any) -> Origin:
        return replace(self, los=self.los | _ids(los))


#: The origin of a name the vault authored (a topic title or id the learner
#: text pipeline did not generate): released as it is, by identity, and only
#: through :meth:`AnswerTextGuard.topic` and :meth:`AnswerTextGuard.lo_ref`.
_AUTHORED = Origin()

#: A provenance node: ``(kind, key)``. ``graded`` (an answer's grading and
#: diagnoses), ``diagnosis``, ``hypothesis``, ``episode``, ``event``,
#: ``belief`` (a registry id of any kind), ``misconception``, ``candidate``,
#: ``gap`` (what a gap's reading drew on) and ``title`` (a generated topic).
_Node = tuple[str, str]


def _ids(values: Iterable[Any]) -> frozenset[str]:
    return frozenset(str(value) for value in values if value)


def _id_list(value: Any) -> list[str] | None:
    """A stored JSON id list; ``[]`` when absent, None when it cannot be read:
    not JSON, not a list, or any member that is not a nonempty string. One
    readable link must not mask an unreadable one (F4 round 4, F3)."""

    if value is None or (isinstance(value, str) and value == ""):
        return []
    try:
        loaded = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return None
    if not isinstance(loaded, list) or not all(isinstance(entry, str) and entry.strip() for entry in loaded):
        return None
    return list(loaded)


def _cited_answers(value: Any) -> list[str] | None:
    """The answers a diagnosis's validated citations name; None when the list,
    or any citation in it, cannot be read (every validated citation names an
    answer: ``diagnosis.split.validation.ValidatedCitation``)."""

    if value is None or (isinstance(value, str) and value == ""):
        return []
    loaded = _loads(value, None) if isinstance(value, str) else value
    if not isinstance(loaded, list):
        return None
    answers: list[str] = []
    for citation in loaded:
        answer = citation.get("attempt_id") if isinstance(citation, Mapping) else None
        if not isinstance(answer, str) or not answer.strip():
            return None
        answers.append(answer)
    return answers


def lo_alias(lo_id: str) -> str:
    """The opaque id that stands for a generated topic while its name is
    withheld: stable across reads, accepted back as a named id
    (:func:`resolve_scope`), and not derived from the topic's words."""

    return LO_ALIAS_PREFIX + hashlib.sha256(str(lo_id).encode("utf-8")).hexdigest()[:16]


class AnswerTextGuard:
    """THE renderer of answer-derived text (spec §4.7 rule 1; F4 rounds 3 and 4).

    One rule for every section: :meth:`render` follows the text's
    :class:`Origin` and releases it (a :class:`GuardedText`) only when

    1. every answer behind it passes the answers' own protection check
       (:meth:`attempt_reason`: exam, reserved, cold-check and probe items, an
       exam or probe attempt, an item the vault cannot read, protection
       unreadable), and so does every item it is about;
    2. the answer keys could be read and the text reproduces none its items
       and topics are known to have had (:class:`KeyBook`);
    3. every answer behind it was graded against exactly one pinned contract
       on its own item (:func:`_pins`), and every item it is about has such an
       answer behind it: the revision is established, not assumed;
    4. every link to those answers could be followed, and there is at least
       one (or the text is about no item at all).

    Otherwise it returns None and the first reason, in that order.

    **Provenance** is a graph (:meth:`closure`), followed transitively with
    cycles (a diagnosis shown a hypothesis whose answer's diagnosis was shown
    the first one) handled: an answer's grading reaches every live diagnosis
    of it and its joint grader's history; a diagnosis reaches everything its
    context receipt says it was shown (answers, hypotheses, recorded beliefs,
    generated topics in its neighbourhood); a belief reaches its error events,
    promotions, error hunts and the gaps that created it; a gap reaches the
    diagnosis it read; a generated topic reaches the gaps that created it.

    **Topic names and ids** (:meth:`topic`, :meth:`lo_ref`) are released here
    too: a prerequisite the learner-text pipeline created has titles drafted
    from the learner's text and ids derived from them, so its name is rendered
    like any other answer-derived text, and while it is withheld its id is an
    opaque alias. A name the vault authored is released as it is.

    Lookups are cached for one read; nothing is written."""

    def __init__(self, connection: Any, withheld: Withheld, book: KeyBook, unknowns: list[str], *,
                 vault: Any = None) -> None:
        self._connection = connection
        self.withheld = withheld
        self.book = book
        self._unknowns = unknowns
        self._vault = vault
        self._attempts: dict[str, dict[str, Any] | None] = {}
        self._pinned: dict[str, Any] = {}
        self._events: dict[str, str | None] = {}
        self._nodes: dict[_Node, tuple[Origin, tuple[_Node, ...]]] = {}
        self._closed: dict[_Node, Origin] = {}
        self._beliefs: dict[tuple[str | None, str], tuple[Any, Any, _Node] | None] = {}
        self._names: dict[str, tuple[GuardedText | None, str | None]] = {}
        self._generated: frozenset[str] | None = None
        self._maps: dict[str, dict[str, Any]] = {}
        self._tables: dict[str, bool] = {}

    def _has(self, table: str) -> bool:
        if table not in self._tables:
            self._tables[table] = _table(self._connection, table)
        return self._tables[table]

    # -- answers ---------------------------------------------------------------

    def _load(self, attempt_ids: Iterable[Any]) -> None:
        wanted = sorted(attempt for attempt in _ids(attempt_ids) if attempt not in self._attempts)
        if not wanted:
            return
        found: dict[str, dict[str, Any] | None] = dict.fromkeys(wanted)
        for start in range(0, len(wanted), _CHUNK):
            chunk = wanted[start:start + _CHUNK]
            for row in self._connection.execute(
                f"SELECT id, practice_item_id, attempt_type, probe_presentation_id, learning_object_id "
                f"FROM practice_attempts WHERE id IN ({_marks(chunk)})", chunk,
            ):
                found[str(row[0])] = {"item": None if row[1] is None else str(row[1]), "type": row[2],
                                      "probe": row[3], "lo": None if row[4] is None else str(row[4])}
        self._attempts.update(found)
        self._pinned.update(_pins(self._connection, {attempt: row["item"] for attempt, row in found.items() if row},
                                  self._unknowns))

    def attempt_reason(self, attempt_id: Any) -> str | None:
        """Why this answer, and everything drawn from it, is protected (the
        answers' own check, for every section), or None."""

        if not self.withheld.available:
            return WITHHELD_UNREADABLE
        self._load([attempt_id])
        row = self._attempts.get(str(attempt_id))
        if row is None:
            return ANSWER_UNRECORDED
        if not row["item"]:
            return WITHHELD_UNKNOWN_ITEM
        reason = self.withheld.reason(row["item"])
        if reason:
            return reason
        if row["type"] in _EXAM_ATTEMPT_TYPES:
            return WITHHELD_EXAM
        if row["type"] == "diagnostic_probe" or row["probe"]:
            return WITHHELD_PROBE
        return None

    def pinned_prompt(self, attempt_id: Any) -> str | None:
        """The prompt of the contract this answer was graded against (the
        question as graded), or None."""

        self._load([attempt_id])
        return self._pinned.get(str(attempt_id))

    # -- the renderer ----------------------------------------------------------

    def render(self, text: Any, origin: Origin, limit: int) -> tuple[GuardedText | None, str | None]:
        """``(text, None)`` released, or ``(None, why)``; ``(None, None)`` for no text."""

        if text is None or not str(text).strip():
            return None, None
        if origin is _AUTHORED:
            # A topic name or id the vault authored (topic / lo_ref only).
            return GuardedText(excerpt(text, limit), _RELEASE), None
        self._load(origin.attempts)
        for attempt_id in sorted(origin.attempts):
            reason = self.attempt_reason(attempt_id)
            if reason:
                return None, f"withheld: {reason}"
        for item_id in sorted(origin.items):
            reason = self.withheld.reason(item_id)
            if reason:
                return None, f"withheld: {reason}"
        if not self.withheld.available:
            return None, f"withheld: {WITHHELD_UNREADABLE}"
        if self.book.unreadable:
            return None, KEYS_UNREADABLE
        if leaks_key(str(text), self._keys(origin)):
            return None, KEY_WITHHELD
        if any(attempt_id not in self._pinned for attempt_id in origin.attempts):
            return None, REVISION_UNKNOWN if origin.direct else REVISION_UNKNOWN_BEHIND
        graded = {self._attempts[attempt_id]["item"] for attempt_id in origin.attempts}
        if origin.items - graded:
            return None, REVISION_UNKNOWN_BEHIND if origin.attempts else REVISION_UNKNOWN_ASKED
        if origin.missing:
            return None, PROVENANCE_MISSING
        if not (origin.attempts or origin.items or origin.unattached):
            return None, PROVENANCE_UNKNOWN
        return GuardedText(excerpt(text, limit), _RELEASE), None

    def _keys(self, origin: Origin) -> list[Any]:
        """Every key of every item behind the text (its answers' items and the
        items it is about), and of every topic it is about: a statement may
        restate any key of its topic, an answer (and the learner's own words
        about one item) is checked against its item's keys, as before."""

        rows = [row for attempt_id in sorted(origin.attempts) if (row := self._attempts.get(attempt_id))]
        items = sorted(set(origin.items) | {row["item"] for row in rows if row["item"]})
        return [key for item_id in items for key in self.book.item(item_id)] + self.book.los(sorted(origin.los))

    # -- topic names and ids (F4 round 4) ----------------------------------------

    def _lo(self, lo_id: str) -> Any:
        return (getattr(self._vault, "learning_objects", None) or {}).get(lo_id)

    def _generated_ids(self) -> frozenset[str]:
        """Every topic the learner-text pipeline created: by its provenance
        (``vault.lifecycle.created_from_learner_text``), its id's form, or a
        gap that records creating it."""

        if self._generated is None:
            from learnloop.vault.lifecycle import created_from_learner_text

            los = getattr(self._vault, "learning_objects", None) or {}
            found = {str(lo_id) for lo_id, lo in los.items()
                     if created_from_learner_text(lo) or str(lo_id).startswith(_GENERATED_LO_PREFIX)}
            self._generated = frozenset(found | set(self._map("gaps_by_created_lo")))
        return self._generated

    def generated(self, lo_id: Any) -> bool:
        key = str(lo_id or "")
        return bool(key) and (key.startswith(_GENERATED_LO_PREFIX) or key in self._generated_ids())

    def _name(self, lo_id: str) -> tuple[GuardedText | None, str | None]:
        """A topic's name released, or why not. A generated topic's title (or,
        when it has left the vault, its id) is answer-derived text with the
        provenance of its drafting; its id carries a slug of that title, so
        the id's words pass the same check."""

        if lo_id not in self._names:
            lo = self._lo(lo_id)
            title = lo.title if lo is not None and str(lo.title or "").strip() else lo_id
            if not self.generated(lo_id):
                self._names[lo_id] = self.render(title, _AUTHORED, TITLE_LIMIT)
            else:
                origin = self.closure(("title", lo_id))
                shown, note = self.render(title, origin, TITLE_LIMIT)
                if shown is not None:
                    words, note = self.render(lo_id.replace("_", " "), origin, _ID_LIMIT)
                    shown = shown if words is not None else None
                self._names[lo_id] = (shown, note)
        return self._names[lo_id]

    def topic(self, lo_id: Any) -> str | None:
        """THE renderer of a topic's name: released (a :class:`GuardedText`),
        or :data:`TOPIC_WITHHELD` and why."""

        if not lo_id:
            return None
        shown, note = self._name(str(lo_id))
        return shown if shown is not None else f"{TOPIC_WITHHELD} {note or PROVENANCE_UNKNOWN}"

    def lo_ref(self, lo_id: Any) -> str | None:
        """THE renderer of a topic's id: released (a :class:`GuardedText`), or
        an opaque alias (:func:`lo_alias`) while a generated topic's name is
        withheld."""

        if not lo_id:
            return None
        key = str(lo_id)
        if self.generated(key) and self._name(key)[0] is None:
            return lo_alias(key)
        return self.render(key, _AUTHORED, _ID_LIMIT)[0]

    def aliases(self) -> dict[str, str]:
        """``{alias: topic id}`` for every generated topic (a named id the
        frontend may send back)."""

        return {lo_alias(lo_id): lo_id for lo_id in self._generated_ids()}

    def searchable(self, lo_id: Any) -> bool:
        """Whether a topic search may match this topic's words: not while a
        generated name is withheld (the match would confirm its words)."""

        return not self.generated(lo_id) or self._name(str(lo_id))[0] is not None

    # -- provenance --------------------------------------------------------------

    def answer(self, attempt_id: Any) -> Origin:
        """An answer's own text."""

        return Origin(attempts=_ids([attempt_id]), missing=not attempt_id, direct=True)

    def gap_words(self, row: Mapping[str, Any]) -> Origin:
        """A learner-text gap's words: the answer they are (a diagnosis or a
        stuck answer) or were asked during, else the item they are about (no
        graded answer behind them), else nothing (a Reader or library
        question)."""

        attempt_id, item_id = row.get("attempt_id"), row.get("practice_item_id")
        answer = row.get("source_kind") in _ANSWER_SOURCES
        if attempt_id:
            return Origin(attempts=_ids([attempt_id]), items=_ids([item_id]), direct=answer)
        if answer:
            return Origin(items=_ids([item_id]), missing=True)
        if item_id:
            return Origin(items=_ids([item_id]))
        # Words tied to no item: filtered by every key of their topic.
        return Origin(unattached=True).about(row.get("anchor_learning_object_id"))

    def diagnosis(self, attempt_id: Any, diagnosis_id: Any) -> Origin:
        """A diagnosis summary of one answer: that answer and everything the
        diagnosis was shown, followed transitively (its own text, the note
        naming "this answer", when it was shown nothing else)."""

        origin = self.closure(("diagnosis", str(diagnosis_id or ""))) | Origin(
            attempts=_ids([attempt_id]), missing=not attempt_id)
        if not (origin.attempts - _ids([attempt_id]) or origin.items):
            return replace(origin, direct=True)
        return origin

    def registry(self, kind: str | None, record_id: Any) -> tuple[Any, Any, Origin] | None:
        """A belief by id, ``(statement, its topic, origin)``: a recorded
        misconception (``durable``), a candidate in the holding pen or a
        hypothesis it projects as one (``candidate``), or any of them (None,
        as a diagnosis's context lists them). None when it is not on record."""

        found = self._belief(kind, record_id)
        if found is None:
            return None
        statement, lo_id, node = found
        return statement, lo_id, self.closure(node)

    def closure(self, root: _Node) -> Origin:
        """Everything ``root``'s text was drawn from: the union of the local
        origins of every node it reaches. Cycles are handled (Tarjan's strongly
        connected components, iteratively): every node of a component gets the
        whole component's closure, so a closure is complete whichever node is
        read first. Cached for this read."""

        if root in self._closed:
            return self._closed[root]
        index: dict[_Node, int] = {}
        low: dict[_Node, int] = {}
        stack: list[_Node] = []
        on_stack: set[_Node] = set()
        work: list[tuple[_Node, Iterator[_Node]]] = []

        def enter(node: _Node) -> None:
            index[node] = low[node] = len(index)
            stack.append(node)
            on_stack.add(node)
            work.append((node, iter(self._node(node)[1])))

        enter(root)
        while work:
            node, successors = work[-1]
            for successor in successors:
                if successor in self._closed:
                    continue
                if successor not in index:
                    enter(successor)
                    break
                if successor in on_stack:
                    low[node] = min(low[node], index[successor])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    members: set[_Node] = set()
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        members.add(member)
                        if member == node:
                            break
                    origin = Origin()
                    for member in members:
                        local, outgoing = self._node(member)
                        origin = origin | local
                        for successor in outgoing:
                            if successor not in members:
                                origin = origin | self._closed[successor]
                    for member in members:
                        self._closed[member] = origin
        return self._closed[root]

    def _node(self, node: _Node) -> tuple[Origin, tuple[_Node, ...]]:
        """A node's own origin and the nodes it links to, read once."""

        if node not in self._nodes:
            kind, key = node
            local, successors = getattr(self, f"_local_{kind}")(key)
            self._nodes[node] = (local, tuple(dict.fromkeys(successors)))
        return self._nodes[node]

    def _local_graded(self, attempt_id: str) -> tuple[Origin, list[_Node]]:
        """Text drawn from an answer's grading or diagnosis (a cause on its
        error events, a hypothesis, a belief normalized from them): the
        answer, the prior answers its joint grader was shown (the C4 history),
        its topic's name when that topic was generated, and everything each of
        its completed live diagnoses was shown. The
        overlay lays a diagnosis's causes on the answer's events, the factor
        projection, the normalizer and the gap pipeline read them, and what an
        earlier diagnosis supplied stays in the beliefs drawn from it, so a
        superseded diagnosis counts too."""

        history = self._map("c4_history").get(attempt_id, [])
        origin = Origin(attempts=_ids([attempt_id]) | _ids(history or ()), missing=not attempt_id or history is None)
        successors: list[_Node] = [("diagnosis", str(diagnosis)) for diagnosis in self._map(
            "diagnoses_by_attempt").get(attempt_id, ())]
        # Its grader was shown its topic: a generated topic's name is drawn on too.
        self._load([attempt_id])
        lo_id = (self._attempts.get(attempt_id) or {}).get("lo")
        if lo_id and self.generated(lo_id):
            successors.append(("title", lo_id))
        return origin, successors

    def _local_diagnosis(self, diagnosis_id: str) -> tuple[Origin, list[_Node]]:
        """What one diagnosis was shown, from its context receipt: its answer,
        the answers it saw, cited or names, the hypotheses and recorded beliefs
        it was given, and the generated topics in its neighbourhood. No
        receipt, or a list in it that cannot be read: what it saw is not
        recorded (a missing link)."""

        row = self._connection.execute(
            "SELECT attempt_id, proposal_json FROM attempt_diagnoses WHERE id = ?", (diagnosis_id,),
        ).fetchone() if diagnosis_id and self._has("attempt_diagnoses") else None
        if row is None:
            return Origin(missing=True), []
        own = Origin(attempts=_ids([row[0]]), missing=not row[0])
        receipt = self._connection.execute(
            "SELECT failure_attempt_ids_json, success_attempt_ids_json, hypothesis_ids_json, "
            "registry_candidate_ids_json, validated_citations_json, retrieval_json, prerequisite_refs_json "
            "FROM diagnosis_context_receipts WHERE diagnosis_id = ?", (diagnosis_id,),
        ).fetchone() if self._has("diagnosis_context_receipts") else None
        if receipt is None:
            return replace(own, missing=True), []
        failures, successes, hypotheses, registry = (_id_list(receipt[index]) for index in range(4))
        cited = _cited_answers(receipt[4])
        retrieval = _loads(receipt[5], None)
        shown = retrieval if isinstance(retrieval, Mapping) else {}
        history = _id_list(shown.get("history_attempt_ids")) if isinstance(retrieval, Mapping) else None
        neighbours = _id_list(shown.get("neighborhood_learning_object_ids"))
        prerequisites = _id_list(receipt[6])
        lists = (failures, successes, hypotheses, registry, cited, history, neighbours, prerequisites)
        if any(listed is None for listed in lists):
            return replace(own, missing=True), []
        proposal = _loads(row[1], None)
        analysis = proposal.get("analysis_md") if isinstance(proposal, Mapping) else None
        named = set(_RECORD_ID.findall(analysis if isinstance(analysis, str) else ""))
        self._load(named)
        answers = [*(failures or ()), *(successes or ()), *(history or ()), *(cited or ()),
                   *(record for record in named if self._attempts.get(record) is not None)]
        successors: list[_Node] = [("hypothesis", hypothesis) for hypothesis in hypotheses or ()]
        successors += [("belief", record) for record in registry or ()]
        successors += [("title", lo_id) for lo_id in [*(neighbours or ()), *(prerequisites or ())]
                       if self.generated(lo_id)]
        return own | Origin(attempts=_ids(answers)), successors

    def _local_hypothesis(self, hypothesis_id: str) -> tuple[Origin, list[_Node]]:
        """A hypothesis statement: its answer's grading, its own error event
        when on record (a regrade replaces events with new ids; the event
        belongs to its answer, so nothing is lost), and its whole episode."""

        row = self._connection.execute(
            "SELECT attempt_id, error_event_id, episode_key, learning_object_id FROM causal_hypotheses WHERE id = ?",
            (hypothesis_id,),
        ).fetchone() if hypothesis_id and self._has("causal_hypotheses") else None
        if row is None:
            return Origin(missing=True), []
        attempt_id, event_id, episode_key, lo_id = row
        successors: list[_Node] = [("graded", str(attempt_id))] if attempt_id else []
        event_answer = self._event_answer(event_id) if event_id else None
        if event_answer:
            successors.append(("graded", event_answer))
        successors.append(("episode", str(episode_key or "")))
        return Origin(los=_ids([lo_id]), missing=not attempt_id), successors

    def _local_episode(self, episode_key: str) -> tuple[Origin, list[_Node]]:
        """Every answer of a hypothesis episode (every version), and the
        answers of their error events that are on record."""

        rows = list(self._connection.execute(
            "SELECT attempt_id, error_event_id FROM causal_hypotheses WHERE episode_key = ?", (episode_key,),
        )) if episode_key and self._has("causal_hypotheses") else []
        successors: list[_Node] = [("graded", str(row[0])) for row in rows if row[0]]
        self._event_answers(row[1] for row in rows if row[1])
        successors += [("graded", answer) for row in rows if row[1] and (answer := self._events.get(str(row[1])))]
        return Origin(missing=not rows or any(not row[0] for row in rows)), successors

    def _local_event(self, event_id: str) -> tuple[Origin, list[_Node]]:
        """An error event a belief lists: its answer's grading; an event not on
        record, or naming no answer, is a missing link."""

        answer = self._event_answer(event_id)
        return (Origin(missing=True), []) if answer is None else (Origin(), [("graded", answer)])

    def _local_belief(self, record_id: str) -> tuple[Origin, list[_Node]]:
        """A registry id as a diagnosis's context lists it (any kind)."""

        found = self._belief(None, record_id)
        return (Origin(missing=True), []) if found is None else (Origin(), [found[2]])

    def _local_misconception(self, misconception_id: str) -> tuple[Origin, list[_Node]]:
        """A recorded misconception (statement and correction): the error
        events it was normalized from or linked to, and the candidates and
        hypotheses promoted into it."""

        row = self._connection.execute(
            "SELECT learning_object_id, source_error_event_ids_json FROM misconceptions WHERE id = ?",
            (misconception_id,),
        ).fetchone() if misconception_id and self._has("misconceptions") else None
        if row is None:
            return Origin(missing=True), []
        lo_id, listed = row[0], _id_list(row[1])
        promotions = self._map("hypotheses_by_promotion")
        successors: list[_Node] = [("event", event_id) for event_id in [
            *(listed or ()), *self._map("events_by_misconception").get(misconception_id, ())]]
        successors += [("candidate", candidate) for candidate in self._map("candidates_by_promotion").get(
            misconception_id, ())]
        successors += [("hypothesis", hypothesis) for hypothesis in promotions.get(misconception_id, ())]
        # A promotion that cannot be read: any belief on its topic may be drawn from it.
        return Origin(los=_ids([lo_id]), missing=listed is None or f"*{lo_id}" in promotions), successors

    def _local_candidate(self, candidate_id: str) -> tuple[Origin, list[_Node]]:
        """A candidate belief: its error events, the items it was seen on, the
        error hunts that minted or counted it, the gaps that created it."""

        row = self._connection.execute(
            "SELECT learning_object_id, source_error_event_ids_json, item_ids_json FROM misconception_candidates "
            "WHERE id = ?", (candidate_id,),
        ).fetchone() if candidate_id and self._has("misconception_candidates") else None
        if row is None:
            return Origin(missing=True), []
        events, items = _id_list(row[1]), _id_list(row[2])
        hunts = self._map("hunts_by_candidate").get(candidate_id, ())
        successors: list[_Node] = [("event", event_id) for event_id in events or ()]
        successors += [("graded", str(attempt_id)) for attempt_id in hunts if attempt_id]
        successors += [("gap", gap_id) for gap_id in self._map("gaps_by_candidate").get(candidate_id, ())]
        missing = events is None or items is None or not all(hunts)
        return Origin(items=_ids(items or ()), los=_ids([row[0]]), missing=missing), successors

    def _local_gap(self, gap_id: str) -> tuple[Origin, list[_Node]]:
        """What a gap's reading drew on (the belief it created, the topic it
        drafted): its words (:meth:`gap_words`), the topic it is anchored on
        when that topic was itself generated, and, when it read a diagnosis
        (``source_id``), everything that diagnosis was shown."""

        row = self._connection.execute(
            "SELECT source_kind, source_id, attempt_id, practice_item_id, anchor_learning_object_id "
            "FROM learner_text_gaps WHERE id = ?", (gap_id,),
        ).fetchone() if gap_id and self._has("learner_text_gaps") else None
        if row is None:
            return Origin(missing=True), []
        values = dict(zip(("source_kind", "source_id", "attempt_id", "practice_item_id",
                           "anchor_learning_object_id"), row, strict=True))
        words = replace(self.gap_words(values), direct=False)
        # Its reader (and a drafter) was shown the topic it is anchored on.
        anchor = values["anchor_learning_object_id"]
        successors: list[_Node] = [("title", str(anchor))] if anchor and self.generated(anchor) else []
        if values["source_kind"] != "diagnosis":
            return words, successors
        if not values["source_id"]:
            return replace(words, missing=True), successors
        return words, [*successors, ("diagnosis", str(values["source_id"]))]

    def _local_title(self, lo_id: str) -> tuple[Origin, list[_Node]]:
        """A generated topic's name (its concept's and LO's titles, and the ids
        derived from them): the gaps that created it, and every generated
        topic sharing a subject that was created no later (its drafter is
        shown the subject's concepts). No gap behind it: what it was drafted
        from is not recorded."""

        lo = self._lo(lo_id)
        gaps = list(self._map("gaps_by_created_lo").get(lo_id, ()))
        extra = getattr(getattr(lo, "provenance", None), "model_extra", None) or {}
        if extra.get("learner_text"):
            gaps += self._map("gaps_by_source").get(str(extra["learner_text"]), ())
        successors: list[_Node] = [("gap", str(gap_id)) for gap_id in gaps]
        if lo is not None:
            subjects = set(lo.subjects or ())
            for other_id in sorted(self._generated_ids()):
                other = self._lo(other_id)
                if other_id == lo_id or other is None or not subjects & set(other.subjects or ()):
                    continue
                if lo.created_at and other.created_at and str(other.created_at) > str(lo.created_at):
                    continue
                successors.append(("title", other_id))
        return Origin(missing=not gaps), successors

    def _belief(self, kind: str | None, record_id: Any) -> tuple[Any, Any, _Node] | None:
        key = (kind, str(record_id or ""))
        if key in self._beliefs:
            return self._beliefs[key]
        connection = self._connection
        found: tuple[Any, Any, _Node] | None = None
        if key[1] and kind in ("durable", None) and self._has("misconceptions"):
            row = connection.execute("SELECT statement, learning_object_id FROM misconceptions WHERE id = ?",
                                     (key[1],)).fetchone()
            if row is not None:
                found = row[0], row[1], ("misconception", key[1])
        if found is None and key[1] and kind in ("candidate", None):
            if self._has("misconception_candidates"):
                row = connection.execute(
                    "SELECT statement, learning_object_id FROM misconception_candidates WHERE id = ?", (key[1],),
                ).fetchone()
                if row is not None:
                    found = row[0], row[1], ("candidate", key[1])
            if found is None and self._has("causal_hypotheses"):
                row = connection.execute("SELECT statement, learning_object_id FROM causal_hypotheses WHERE id = ?",
                                         (key[1],)).fetchone()
                if row is not None:
                    found = row[0], row[1], ("hypothesis", key[1])
        self._beliefs[key] = found
        return found

    def _event_answers(self, event_ids: Iterable[Any]) -> None:
        """Read the answers behind error events into the cache (None: not on
        record, or naming no answer)."""

        wanted = sorted(event_id for event_id in _ids(event_ids) if event_id not in self._events)
        if not wanted:
            return
        found: dict[str, str | None] = dict.fromkeys(wanted)
        if self._has("error_events"):
            for start in range(0, len(wanted), _CHUNK):
                chunk = wanted[start:start + _CHUNK]
                for event_id, attempt_id in self._connection.execute(
                    f"SELECT id, attempt_id FROM error_events WHERE id IN ({_marks(chunk)})", chunk,
                ):
                    found[str(event_id)] = str(attempt_id) if attempt_id else None
        self._events.update(found)

    def _event_answer(self, event_id: Any) -> str | None:
        self._event_answers([event_id])
        return self._events.get(str(event_id or ""))

    def _map(self, name: str) -> dict[str, Any]:
        """One-query links, read once: which error events, candidates and
        hypotheses a misconception was promoted from or normalized out of,
        which error hunts and gaps created a candidate, which gaps created a
        topic, an answer's live diagnoses and its joint grader's history."""

        if name in self._maps:
            return self._maps[name]
        found: dict[str, Any] = {}
        connection = self._connection
        if name == "events_by_misconception" and self._has("error_events"):
            for misconception_id, event_id in connection.execute(
                "SELECT misconception_id, id FROM error_events WHERE misconception_id IS NOT NULL"
            ):
                found.setdefault(str(misconception_id), []).append(str(event_id))
        elif name == "candidates_by_promotion" and self._has("misconception_candidates"):
            for candidate_id, promoted in connection.execute(
                "SELECT id, promoted_misconception_id FROM misconception_candidates "
                "WHERE promoted_misconception_id IS NOT NULL"
            ):
                found.setdefault(str(promoted), []).append(str(candidate_id))
        elif name == "hypotheses_by_promotion" and self._has("causal_hypotheses"):
            for hypothesis_id, lo_id, evidence in connection.execute(
                "SELECT id, learning_object_id, evidence_json FROM causal_hypotheses "
                "WHERE evidence_json LIKE '%promoted_misconception_id%'"
            ):
                promoted = _loads(evidence, None)
                if not isinstance(promoted, Mapping):
                    found.setdefault(f"*{lo_id}", []).append(str(hypothesis_id))
                elif promoted.get("promoted_misconception_id"):
                    found.setdefault(str(promoted["promoted_misconception_id"]), []).append(str(hypothesis_id))
        elif name == "hunts_by_candidate" and self._has("error_hunt_outcomes"):
            for candidate_id, attempt_id in connection.execute(
                "SELECT misconception_candidate_id, attempt_id FROM error_hunt_outcomes "
                "WHERE misconception_candidate_id IS NOT NULL"
            ):
                found.setdefault(str(candidate_id), []).append(attempt_id)
        elif name == "gaps_by_candidate" and self._has("learner_text_gaps"):
            for gap_id, target_id in connection.execute(
                "SELECT id, target_id FROM learner_text_gaps WHERE target_kind = 'candidate' "
                "AND action = 'belief_candidate'"
            ):
                found.setdefault(str(target_id), []).append(str(gap_id))
        elif name == "gaps_by_created_lo" and self._has("learner_text_gaps"):
            for gap_id, created, target_id in connection.execute(
                "SELECT id, created_learning_object_id, CASE WHEN action = 'created_prerequisite' AND "
                "target_kind = 'learning_object' THEN target_id END FROM learner_text_gaps "
                "WHERE created_learning_object_id IS NOT NULL OR action = 'created_prerequisite'"
            ):
                for lo_id in {created, target_id} - {None, ""}:
                    found.setdefault(str(lo_id), []).append(str(gap_id))
        elif name == "gaps_by_source" and self._has("learner_text_gaps"):
            for gap_id, kind, source_id in connection.execute(
                "SELECT id, source_kind, source_id FROM learner_text_gaps"
            ):
                found.setdefault(f"{kind}:{source_id}", []).append(str(gap_id))
        elif name == "diagnoses_by_attempt" and self._has("attempt_diagnoses"):
            for diagnosis_id, attempt_id in connection.execute(
                "SELECT id, attempt_id FROM attempt_diagnoses WHERE mode = 'live' "
                "AND (status = 'completed' OR causal_view_json IS NOT NULL) ORDER BY created_at, id"
            ):
                found.setdefault(str(attempt_id), []).append(str(diagnosis_id))
        elif name == "c4_history" and self._has("diagnostic_augmentation_receipts"):
            for attempt_id, history in connection.execute(
                "SELECT attempt_id, c4_history_attempt_ids_json FROM diagnostic_augmentation_receipts"
            ):
                found[str(attempt_id)] = _id_list(history)
        self._maps[name] = found
        return found


#: Every text field of ``learning_context``'s output (``ContextOut`` in
#: ``learnloop_mcp.server``), by path: ``section[].field``, ``[]`` for a list,
#: a union entry by its kind (``open_hypotheses[diagnosed_cause].statement``).
#: These are drawn from an answer or an error event and are released only by
#: :meth:`AnswerTextGuard.render` (a :class:`GuardedText` or None).
ANSWER_DERIVED_FIELDS: frozenset[str] = frozenset({
    "misconceptions[].statement",
    "misconceptions[].correction",
    "misconception_candidates[].statement",
    "open_hypotheses[diagnosed_cause].statement",
    "recurrence_groups[].statement",
    "recent_answer_traces[].answer",
    "recent_answer_traces[].diagnosis.summary",
    "recent_answer_traces[].diagnosis.hypotheses[]",
    "open_learner_text_gaps[].learner_text",
    "open_learner_text_gaps[].target",
})
#: Every topic name (F4 round 4). The vault's titles, but the learner-text
#: pipeline drafts a missing prerequisite's titles from the learner's text,
#: so each is released only by :meth:`AnswerTextGuard.topic` (a
#: :class:`GuardedText`), or is :data:`TOPIC_WITHHELD` and why.
TOPIC_FIELDS: frozenset[str] = frozenset({
    "misconceptions[].topic",
    "misconception_candidates[].topic",
    "open_hypotheses[diagnosed_cause].topic",
    "open_hypotheses[unresolved_cause].topic",
    "recurrence_groups[].topics[]",
    "recent_answer_traces[].topic",
    "open_learner_text_gaps[].topic",
    "open_learner_text_gaps[].target_topic",
    "retention_risks[].topic",
})
#: Every topic id (F4 round 4): a generated prerequisite's id carries a slug of
#: its drafted title (``lo_ltg_<slug>_<hash>``), so each is released only by
#: :meth:`AnswerTextGuard.lo_ref` (a :class:`GuardedText`), or is an opaque
#: :data:`LO_ALIAS_PREFIX` alias while the name is withheld.
TOPIC_ID_FIELDS: frozenset[str] = frozenset({
    "scope.learning_object_ids[]",
    "misconceptions[].learning_object_id",
    "misconception_candidates[].learning_object_id",
    "open_hypotheses[diagnosed_cause].learning_object_id",
    "open_hypotheses[unresolved_cause].learning_object_id",
    "recurrence_groups[].learning_object_ids[]",
    "recent_answer_traces[].learning_object_id",
    "open_learner_text_gaps[].learning_object_id",
    "retention_risks[].learning_object_id",
})
_ID, _TIME, _ENUM, _NOTE = ("a record id (a ULID, or a digest for a group key)", "a timestamp",
                            "a stored code (an enumeration)", "a fixed note")
#: Every other text field, and why it is not answer-derived by construction.
NON_ANSWER_FIELDS: Mapping[str, str] = {
    "context_version": _NOTE, "as_of": _TIME, "unknowns[]": _NOTE,
    "scope.matched_by": _ENUM, "scope.unknown_ids[]": "the request's own ids",
    "scope.topic": "the request's own words",
    "labels.evidence": _NOTE, "labels.hypotheses": _NOTE, "labels.held_for_review": _NOTE,
    "labels.recall_now": _NOTE,
    "misconceptions[].misconception_id": _ID,
    "misconceptions[].status": _ENUM, "misconceptions[].statement_note": _NOTE,
    "misconceptions[].correction_note": _NOTE, "misconceptions[].since": _TIME, "misconceptions[].updated_at": _TIME,
    "misconception_candidates[].candidate_id": _ID,
    "misconception_candidates[].status": _ENUM,
    "misconception_candidates[].statement_note": _NOTE, "misconception_candidates[].note": _NOTE,
    "misconception_candidates[].since": _TIME, "misconception_candidates[].updated_at": _TIME,
    "open_hypotheses[diagnosed_cause].kind": _ENUM,
    "open_hypotheses[diagnosed_cause].status": _ENUM,
    "open_hypotheses[diagnosed_cause].since": _TIME, "open_hypotheses[diagnosed_cause].statement_note": _NOTE,
    "open_hypotheses[diagnosed_cause].hypothesis_id": _ID, "open_hypotheses[diagnosed_cause].attempt_id": _ID,
    "open_hypotheses[diagnosed_cause].error_event_id": _ID,
    "open_hypotheses[diagnosed_cause].promoted_misconception_id": _ID,
    "open_hypotheses[diagnosed_cause].label": _NOTE,
    "open_hypotheses[diagnosed_cause].repairs_tried[].episode_id": _ID,
    "open_hypotheses[diagnosed_cause].repairs_tried[].state": _ENUM,
    "open_hypotheses[diagnosed_cause].repairs_tried[].started_at": _TIME,
    "open_hypotheses[diagnosed_cause].repairs_tried[].completed_at": _TIME,
    "open_hypotheses[unresolved_cause].kind": _ENUM,
    "open_hypotheses[unresolved_cause].status": _ENUM,
    "open_hypotheses[unresolved_cause].since": _TIME,
    "open_hypotheses[unresolved_cause].statement": "a fixed note with a count",
    "recurrence_groups[].group_key": _ID, "recurrence_groups[].statement_note": _NOTE,
    "recurrence_groups[].joined_by[]": _ENUM,
    "recurrence_groups[].label": _NOTE,
    "recent_answer_traces[].attempt_id": _ID, "recent_answer_traces[].at": _TIME,
    "recent_answer_traces[].kind": _ENUM, "recent_answer_traces[].attempt_type": _ENUM,
    "recent_answer_traces[].result": _ENUM, "recent_answer_traces[].graded_by": _ENUM,
    "recent_answer_traces[].cold_check.lane": _ENUM, "recent_answer_traces[].entry_surface": _ENUM,
    "recent_answer_traces[].evidence_origin": _ENUM, "recent_answer_traces[].key_status": _ENUM,
    "recent_answer_traces[].withheld": _NOTE,
    "recent_answer_traces[].stem": "the question as graded (its pinned contract's prompt), never an answer",
    "recent_answer_traces[].stem_note": _NOTE, "recent_answer_traces[].answer_note": _NOTE,
    "recent_answer_traces[].diagnosis.status": _ENUM, "recent_answer_traces[].diagnosis.summary_note": _NOTE,
    "recent_answer_traces[].diagnosis.hypotheses_note": _NOTE,
    "open_learner_text_gaps[].gap_id": _ID, "open_learner_text_gaps[].kind": _ENUM,
    "open_learner_text_gaps[].action": _ENUM,
    "open_learner_text_gaps[].target_kind": _ENUM,
    "open_learner_text_gaps[].target_note": _NOTE,
    "open_learner_text_gaps[].learner_text_note": _NOTE, "open_learner_text_gaps[].source": _ENUM,
    "open_learner_text_gaps[].since": _TIME, "open_learner_text_gaps[].label": _NOTE,
    "retention_risks[].next_due_at": _TIME,
}


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
                  topic: str | None = None, aliases: Mapping[str, str] | None = None,
                  searchable: Callable[[str], bool] | None = None) -> dict[str, Any]:
    """The LOs a context is about: named ids, a topic's matches, or every active LO.

    ``aliases`` (:meth:`AnswerTextGuard.aliases`) resolve the opaque id a
    generated topic is shown under while its name is withheld; ``searchable``
    (:meth:`AnswerTextGuard.searchable`) keeps a topic search from matching
    the words of a withheld name (a match would confirm them)."""

    los = vault.learning_objects
    if learning_object_ids:
        requested = list(dict.fromkeys(learning_object_ids))
        resolved = {lo: (aliases or {}).get(lo, lo) for lo in requested}
        known = list(dict.fromkeys(resolved[lo] for lo in requested if resolved[lo] in los))
        unknown = [lo for lo in requested if resolved[lo] not in los]
        return {"learning_object_ids": known, "matched_by": "ids", "unknown_ids": unknown}
    if topic and topic.strip():
        words = [word for word in _WORD.findall(topic.lower()) if len(word) > 2] or _WORD.findall(topic.lower())
        concepts = getattr(vault, "concepts", {}) or {}
        matched: list[tuple[int, str]] = []
        for lo_id, lo in los.items():
            if lo.status != "active" or (searchable is not None and not searchable(lo_id)):
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


def _misconceptions(connection: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
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
                values = dict(row)
                origin = guard.closure(("misconception", str(values["id"])))
                statement, note = guard.render(values["statement"], origin, STATEMENT_LIMIT)
                correction, correction_note = guard.render(values.get("correction_statement"), origin, STATEMENT_LIMIT)
                sightings = _loads(values["source_error_event_ids_json"], [])
                registry.append({
                    "misconception_id": values["id"],
                    "learning_object_id": guard.lo_ref(values["learning_object_id"]),
                    "topic": guard.topic(values["learning_object_id"]),
                    "status": values["status"], "statement": statement, "statement_note": note,
                    "correction": correction, "correction_note": correction_note,
                    "severity": round(float(values["severity"] or 0.0), 3),
                    "evidence_count": len(sightings) if isinstance(sightings, list) else 0,
                    "since": values["created_at"], "updated_at": values["updated_at"],
                })
        if _table(connection, "misconception_candidates"):
            for row in connection.execute(
                f"SELECT * FROM misconception_candidates WHERE status = 'candidate' "
                f"AND learning_object_id IN ({_marks(scope)}) ORDER BY occurrence_count DESC, updated_at DESC, id",
                scope,
            ):
                values = dict(row)
                statement, note = guard.render(values["statement"], guard.closure(("candidate", str(values["id"]))),
                                               STATEMENT_LIMIT)
                candidates.append({
                    "candidate_id": values["id"],
                    "learning_object_id": guard.lo_ref(values["learning_object_id"]),
                    "topic": guard.topic(values["learning_object_id"]),
                    "status": "candidate", "statement": statement, "statement_note": note,
                    "evidence_count": int(values["occurrence_count"] or 0),
                    "note": "held until it recurs; not yet a recorded misconception",
                    "since": values["created_at"], "updated_at": values["updated_at"],
                })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: misconceptions not read", exc_info=True)
        unknowns.append("misconceptions could not be read")
    return registry[: limits.misconceptions], candidates[: limits.candidates]


def _hypotheses(connection: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
                unknowns: list[str]) -> list[dict[str, Any]]:
    """Open hypotheses: the diagnosed causes, then the unresolved causes (each
    read on its own, so an LO with unresolved causes and no named hypothesis
    still shows them)."""

    if not los:
        return []
    return _share_limit(_diagnosed_causes(connection, los, limits, guard, unknowns),
                        _unresolved_causes(connection, los, guard, unknowns), limits.hypotheses)


def _share_limit(diagnosed: list[dict[str, Any]], unresolved: list[dict[str, Any]],
                 limit: int) -> list[dict[str, Any]]:
    """Both kinds under the one ``limit``. When they overflow it, the
    unresolved causes keep up to half of it (at least one entry), an LO with
    no diagnosed cause shown taking those first, so an LO whose only open
    problem is unsettled stays visible; the diagnosed causes fill the rest."""

    limit = max(int(limit), 0)
    if len(diagnosed) + len(unresolved) <= limit:
        return diagnosed + unresolved
    reserve = min(len(unresolved), max(1, limit // 2)) if limit else 0
    kept = diagnosed[: limit - reserve]
    shown = {entry["learning_object_id"] for entry in kept}
    ranked = sorted(range(len(unresolved)), key=lambda index: unresolved[index]["learning_object_id"] in shown)
    return kept + [unresolved[index] for index in sorted(ranked[: limit - len(kept)])]


def _diagnosed_causes(connection: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
                      unknowns: list[str]) -> list[dict[str, Any]]:
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
            # Drawn from every answer of its episode (every version), their
            # grading and diagnoses, and what those were shown.
            origin = guard.closure(("hypothesis", str(row["id"])))
            statement, note = guard.render(row["statement"], origin, STATEMENT_LIMIT)
            entries.append({
                "kind": "diagnosed_cause", "learning_object_id": guard.lo_ref(row["learning_object_id"]),
                "topic": guard.topic(row["learning_object_id"]),
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


def _unresolved_causes(connection: Any, los: set[str], guard: AnswerTextGuard,
                       unknowns: list[str]) -> list[dict[str, Any]]:
    """Answers whose cause is not settled, per LO (a count; no answer text).
    One entry per LO in scope; :func:`_share_limit` cuts them with the
    diagnosed causes."""

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
                "kind": "unresolved_cause", "learning_object_id": guard.lo_ref(row["learning_object_id"]),
                "topic": guard.topic(row["learning_object_id"]),
                "status": "open", "since": row["since"],
                "statement": f"{row['n']} answer(s) whose cause is not settled",
            })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: unresolved causes not read", exc_info=True)
        unknowns.append("unresolved causes could not be read")
    return entries


def _recurrence_groups(connection: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
                       unknowns: list[str]) -> list[dict[str, Any]]:
    """Groups touching the scope's LOs. An empty scope has none (a topic or
    ids that matched nothing is not a whole-learner request: that scope is
    every active LO). A group's statement is its root's; it is drawn from
    every answer behind every member episode."""

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
        for group_key, rows in selected.items():
            lo_ids = sorted({str(row["learning_object_id"]) for row in rows})
            root = next((row for row in rows if row["episode_key"] == row["root_episode_key"]), rows[0])
            origin = Origin()
            for row in rows:
                origin = origin | guard.closure(("episode", str(row["episode_key"])))
            statement, note = guard.render(root["statement"], origin.about(*lo_ids), STATEMENT_LIMIT)
            groups.append({
                "group_key": group_key, "statement": statement, "statement_note": note,
                "episodes": len(rows), "class_count": max(int(row["class_count"]) for row in rows),
                "joined_by": sorted({str(row["joined_by"]) for row in rows}),
                "learning_object_ids": [guard.lo_ref(lo) for lo in lo_ids],
                "topics": [guard.topic(lo) for lo in lo_ids],
                "label": "the same cause seen more than once",
            })
        groups.sort(key=lambda group: (-group["class_count"], group["group_key"]))
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: recurrence groups not read", exc_info=True)
        unknowns.append("recurrence groups could not be read")
    return groups[: limits.groups]


def _traces(connection: Any, repository: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
            now_iso: str) -> list[dict[str, Any]]:
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
    hypotheses: dict[str, list[dict[str, Any]]] = {}
    if _table(connection, "causal_hypotheses"):
        for row in connection.execute(
            f"SELECT id, attempt_id, statement, learning_object_id FROM causal_hypotheses "
            f"WHERE cause_scope = 'learner_state' AND status IN ('candidate', 'validated') "
            f"AND attempt_id IN ({_marks(ids)}) ORDER BY created_at", ids,
        ):
            hypotheses.setdefault(str(row["attempt_id"]), []).append(dict(row))
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
        # The answers' protection check; the answer itself, like every text
        # drawn from it, goes through the one renderer (pinned revision, keys).
        reason = guard.attempt_reason(attempt_id)
        answer = answer_note = None
        if reason is None:
            answer, answer_note = guard.render(row.get("learner_answer_md"), guard.answer(attempt_id), EXCERPT_LIMIT)
        stem = None if reason else guard.pinned_prompt(attempt_id)
        diagnosis = _diagnosis(repository, guard, attempt_id, hidden=reason is not None,
                               hypotheses=hypotheses.get(attempt_id, []))
        status = row.get("reference_status")
        traces.append({
            "attempt_id": attempt_id, "at": row["created_at"],
            "learning_object_id": guard.lo_ref(row["learning_object_id"]),
            "topic": guard.topic(row["learning_object_id"]),
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


def _diagnosis(repository: Any, guard: AnswerTextGuard, attempt_id: str, *, hidden: bool,
               hypotheses: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
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
        diagnosis_id = str(status["diagnosis_id"])
        diagnosis = repository.attempt_diagnosis(diagnosis_id) or {}
        analysis = str((diagnosis.get("proposal") or {}).get("analysis_md") or "")
        if analysis:
            summary, note = guard.render(plain_summary(repository, analysis), guard.diagnosis(attempt_id, diagnosis_id),
                                         STATEMENT_LIMIT)
            if note:
                entry["summary_note"] = note
    entry["summary"] = summary
    rendered = [guard.render(row["statement"], guard.closure(("hypothesis", str(row["id"]))), STATEMENT_LIMIT)
                for row in hypotheses]
    entry["hypotheses"] = [text for text, _note in rendered if text]
    notes = [note for _text, note in rendered if note]
    if notes:
        entry["hypotheses_note"] = notes[0]
    return entry


def _gaps(connection: Any, los: set[str], limits: ContextLimits, guard: AnswerTextGuard,
          unknowns: list[str]) -> list[dict[str, Any]]:
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
            f"""SELECT id, source_kind, attempt_id, practice_item_id, anchor_learning_object_id, target_kind,
                       target_id, kind, action, learner_text, created_at
                  FROM learner_text_gaps
                 WHERE kind IN ('prerequisite', 'misconception')
                   AND (anchor_learning_object_id IN ({_marks(scope)})
                        OR (target_kind = 'learning_object' AND target_id IN ({_marks(scope)})))
                 ORDER BY created_at DESC, id DESC""",
            (*scope, *scope),
        ):
            if str(row["id"]) in reversed_ids:
                continue
            values = dict(row)
            lo = values["target_id"] if values["target_kind"] == "learning_object" and values["target_id"] in los \
                else values["anchor_learning_object_id"]
            text, note = guard.render(values["learner_text"], guard.gap_words(values), STATEMENT_LIMIT)
            target, target_note, target_topic = _gap_target(guard, values["target_kind"], values["target_id"])
            gaps.append({
                "gap_id": values["id"], "kind": values["kind"], "action": values["action"],
                "learning_object_id": guard.lo_ref(lo), "topic": guard.topic(lo),
                "target_kind": values["target_kind"], "target_topic": target_topic,
                "target": target, "target_note": target_note,
                "learner_text": text, "learner_text_note": note, "source": values["source_kind"],
                "since": values["created_at"],
                "label": "named from the learner's own words; reversible with 'not this'",
            })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: learner-text gaps not read", exc_info=True)
        unknowns.append("open learner-text gaps could not be read")
    return gaps[: limits.gaps]


def _gap_target(guard: AnswerTextGuard, kind: Any,
                target_id: Any) -> tuple[GuardedText | None, str | None, str | None]:
    """What a gap was matched to: ``(statement, note, topic)``. A topic is its
    name (:meth:`AnswerTextGuard.topic`: a prerequisite the gap created was
    named from the learner's text); a recorded misconception or a candidate is
    a statement, released by the same renderer as every other (its own
    origin)."""

    if not kind or not target_id:
        return None, None, None
    if kind == "learning_object":
        return None, None, guard.topic(target_id)
    found = guard.registry(str(kind), target_id) if kind in ("durable", "candidate") else None
    if found is None:
        return None, "the belief it was matched to is not on record", None
    statement, lo_id, origin = found
    shown, note = guard.render(statement, origin, STATEMENT_LIMIT)
    return shown, note, guard.topic(lo_id)


def retention_risks(vault: Any, repository: Any, los: Iterable[str], *, now: datetime, limit: int = 15,
                    unknowns: list[str] | None = None, topic: Callable[[str], Any] | None = None,
                    ref: Callable[[str], Any] | None = None) -> list[dict[str, Any]]:
    """Topics whose modelled recall now is below :data:`RETENTION_TARGET`, or due now.

    FSRS retrievability from each item's stored memory state: a model
    estimate, not a test. Lowest recall first. ``topic`` and ``ref`` name a
    topic in the output (``learning_context`` passes its guard's
    :meth:`AnswerTextGuard.topic` and :meth:`AnswerTextGuard.lo_ref`); by
    default the vault's title and id."""

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
            "learning_object_id": lo_id,
            "recall_now": round(sum(entry["recalls"]) / len(entry["recalls"]), 3),
            "items_below_target": below, "items_due_now": entry["due_now"], "items_tracked": len(entry["recalls"]),
            "next_due_at": entry["next_due_at"],
        })
    risks.sort(key=lambda risk: (risk["recall_now"], risk["learning_object_id"]))
    name = topic or (lambda lo_id: titles.get(lo_id, lo_id))
    ident = ref or (lambda lo_id: lo_id)
    return [{**risk, "learning_object_id": ident(risk["learning_object_id"]), "topic": name(risk["learning_object_id"])}
            for risk in risks[: max(int(limit), 0)]]


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
    unknowns: list[str] = []
    withheld = withheld if withheld is not None else withheld_items(vault, repository)
    unknowns.extend(withheld.unknowns)
    with repository.connection() as connection:
        # Every answer-derived text below, and every topic name and id, is
        # released by this one guard.
        guard = AnswerTextGuard(connection, withheld, key_book(connection, vault, unknowns), unknowns, vault=vault)
        scope = resolve_scope(vault, learning_object_ids=learning_object_ids, topic=topic, aliases=guard.aliases(),
                              searchable=guard.searchable)
        los = set(scope["learning_object_ids"])
        misconceptions, candidates = _misconceptions(connection, los, limits, guard, unknowns)
        hypotheses = _hypotheses(connection, los, limits, guard, unknowns)
        groups = _recurrence_groups(connection, los, limits, guard, unknowns)
        try:
            traces = _traces(connection, repository, los, limits, guard, now_iso)
        except Exception:  # noqa: BLE001 - named as unknown
            _LOG.warning("learner context: answer traces not read", exc_info=True)
            unknowns.append("recent answer traces could not be read")
            traces = []
        gaps = _gaps(connection, los, limits, guard, unknowns)
        risks = retention_risks(vault, repository, los, now=moment, limit=limits.risks, unknowns=unknowns,
                                topic=guard.topic, ref=guard.lo_ref)
        shown_los = [guard.lo_ref(lo_id) for lo_id in scope["learning_object_ids"]]
    if scope["matched_by"] == "topic" and not los:
        unknowns.append("no topic in the vault matched; LearnLoop has no record about it")
    if scope["matched_by"] == "ids" and not los:
        unknowns.append("none of the named learning objects is in this vault; LearnLoop has no record about them")
    return {
        "context_version": CONTEXT_VERSION,
        "as_of": now_iso,
        "scope": {**scope, "learning_object_ids": shown_los, "learning_object_count": len(los)},
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
    "ANSWER_DERIVED_FIELDS",
    "CONTEXT_VERSION",
    "AnswerTextGuard",
    "ContextLimits",
    "GuardedText",
    "KEY_WITHHELD",
    "KeyBook",
    "LO_ALIAS_PREFIX",
    "NON_ANSWER_FIELDS",
    "Origin",
    "PROTECTION_UNKNOWN",
    "RETENTION_TARGET",
    "SNAPSHOT_UNSETTLED",
    "TOPIC_FIELDS",
    "TOPIC_ID_FIELDS",
    "TOPIC_WITHHELD",
    "WITHHELD_UNKNOWN_ITEM",
    "WITHHELD_UNREADABLE",
    "Withheld",
    "excerpt",
    "key_book",
    "leaks_key",
    "learning_context",
    "lo_alias",
    "protection_issues",
    "resolve_scope",
    "retention_risks",
    "withheld_items",
]
