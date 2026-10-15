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

**What leaves LearnLoop: one structural rule** (:class:`TextGuard`; owner
decision 2026-10-14, "land narrow, then fix source"). A text is shown only
when it is

* **(a) authored vault text**: a topic's name or id that the learner or an
  authored vault file wrote, and the question as it was graded (its pinned
  contract's prompt);
* **(b) the learner's own answer on a pinned attempt**, through the answer
  guard: the answer's protection, exactly one pinned contract on its own item
  (the revision it was graded against) and no key its item is known to have
  had (:class:`KeyBook`);
* **(c) a derived text with a recorded, complete write-time provenance whose
  inputs are all safe** (:class:`WriteProvenance`, read through a
  :data:`ProvenanceSource`): the hook for the follow-up desktop stage
  ("diagnosis input provenance"). **No producer records one yet.**

So everything a diagnosis, the grader's normalizer, the gap reader or the
prerequisite drafter wrote, or that was derived from their output, is held
back with one fixed reason (:data:`HELD_BACK`): misconception and candidate
statements and corrections, hypothesis and recurrence-group statements,
diagnosis summaries and their hypotheses, what a learner-text gap was matched
to, the words of a question the learner asked (no pinned answer behind them),
and every generated topic's name, id and seeded question. The entries keep
their structure: ids (a generated topic's id as an opaque keyed alias,
accepted back as a named id), statuses, counts, dates, evidence counts and
held state; recurrence-group keys are keyed digests too (Q13).

Why no output-side provenance: earlier rounds followed each text's provenance
from the output back to the answers behind it, and five reviews in a row found
inputs no record names (a snapshot diagnosis reads the whole-vault export
without recording what it opened; the joint grader's C4 receipt is written
outside the grading transaction). Provenance is now trusted only when it was
recorded when the text was written.

**Protection (unchanged):**

* no answer key, reference solution, rubric or hint is ever read into the
  output;
* exam and held-out material (``exam_material.item_exam_status``, every
  provenance form), items reserved for an assessment or a held-out exam,
  items held by an open cold check or a repair's cold retry, and diagnostic
  probes (:func:`withheld_items`) keep their result but never show a question
  or an answer; nor does an item the vault cannot read (deleted, or its file
  unreadable). When the predicates cannot be read, including a source-sets
  file the loader could not read or a vault snapshot that changed while it
  loaded (:func:`protection_issues`), no question or answer shows at all
  (fail closed);
* a grade held for review (THE predicate, ``held_grades``) is "held for
  review", never a score;
* a question is the prompt of the attempt's pinned assessment contract (the
  revision it was graded against), never today's edited prompt.

Nothing here is evidence: every label (assisted, cold, held) is read from the
ledger that owns it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
from collections.abc import Callable, Iterable, Mapping, Sequence
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

#: THE reason a derived text is withheld: nothing recorded, when it was
#: written, what it was written from (rule (c) has no record to check).
HELD_BACK = "Held back until LearnLoop records what this was written from"

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
STEM_UNRECORDED = "question revision not recorded"
ANSWER_UNRECORDED = "an answer it was drawn from is not on record"
PINS_UNREADABLE = ("the question revisions past answers were graded against could not be read: no question or "
                   "answer is shown")
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


def _ids(values: Iterable[Any]) -> frozenset[str]:
    return frozenset(str(value) for value in values if value)


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
        unknowns.append("past answer keys could not be read: answers that could quote one are withheld")
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
    except Exception:  # noqa: BLE001 - named as unknown; no answer shows
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


# -- what may be released: the one rule ---------------------------------------------


_RELEASE = object()


class GuardedText(str):
    """Text :class:`TextGuard` released, and only it: the constructor takes a
    module-private token. Each rule has its own type, built in one method
    only (a test pins it): :class:`AuthoredText` (a), :class:`AnswerText` (b),
    :class:`RecordedText` (c). Copies and pickles are plain ``str``."""

    __slots__ = ()

    def __new__(cls, value: str, token: object) -> GuardedText:
        if token is not _RELEASE or cls is GuardedText:
            raise TypeError("text is released only by TextGuard, one rule per type")
        return super().__new__(cls, value)

    def __reduce__(self) -> tuple[Any, ...]:
        return (str, (str(self),))


class AuthoredText(GuardedText):
    """(a) Authored vault text: a topic's name or id the learner or an
    authored vault file wrote, or the question as graded."""

    __slots__ = ()


class AnswerText(GuardedText):
    """(b) The learner's own answer on a pinned attempt."""

    __slots__ = ()


class RecordedText(GuardedText):
    """(c) A derived text whose recorded write-time provenance names only safe inputs."""

    __slots__ = ()


@dataclass(frozen=True)
class WriteProvenance:
    """What one derived text was written from, recorded when it was written.

    The hook for the follow-up desktop stage ("diagnosis input provenance"):
    the writer (a diagnosis, the normalizer, the gap reader, the drafter)
    records, in the transaction that writes the text, every input it read:
    the answers (``answers``), the practice items whose question or key it
    saw (``items``) and the topics whose names it saw (``topics``). The
    record is closed: a writer that read another derived text records that
    text's own inputs. ``complete`` is the writer's statement that nothing
    else was read (a snapshot export it could not account for, a history it
    did not record, makes it False). **No producer writes one yet**, so
    :func:`no_write_provenance` is the only source in use."""

    complete: bool
    answers: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()

    def readable(self) -> bool:
        """Complete, every input an id, and at least one input."""

        lists = (self.answers, self.items, self.topics)
        return (self.complete is True and all(isinstance(values, tuple) for values in lists)
                and all(isinstance(value, str) and value.strip() for values in lists for value in values)
                and any(lists))


#: Where a derived text's write-time record is read from:
#: ``(connection, kind, record id) -> WriteProvenance | None``. The kinds are
#: :data:`DERIVED_KINDS`.
ProvenanceSource = Callable[[Any, str, str], WriteProvenance | None]

#: The derived texts (c) covers, by record kind.
DERIVED_KINDS: Mapping[str, str] = {
    "misconception": "a recorded misconception's statement",
    "misconception_correction": "a recorded misconception's correction",
    "candidate": "a candidate belief's statement",
    "hypothesis": "a hypothesis statement (and a recurrence group's, its root's)",
    "diagnosis": "a diagnosis summary",
    "learner_text_gap": "the words of a learner-text gap not drawn from a pinned answer (a question)",
    "learning_object": "a generated topic's name and id",
    "practice_item": "the question of an item seeded on a generated topic",
}


def no_write_provenance(_connection: Any, _kind: str, _record_id: str) -> None:
    """Today's source: nothing records a derived text's inputs when it is written."""

    return None


# -- aliases: opaque, keyed ---------------------------------------------------------


#: What stands for a generated topic's id while its name is withheld.
LO_ALIAS_PREFIX = "lo_withheld_"
#: What stands for a recurrence group's stored key (Q13).
GROUP_ALIAS_PREFIX = "rg_"
#: What stands for a generated topic's name while it is withheld; the reason follows in brackets.
TOPIC_WITHHELD = "a topic named from the learner's own words"
_ALIAS_HEX = 20
#: The key for a process with no vault key (``RemoteRuntime.alias_key``): aliases
#: are stable for this process and cannot be recomputed by a client either way.
_PROCESS_ALIAS_KEY = secrets.token_bytes(32)


def _keyed(key: bytes | None, kind: str, value: str) -> str:
    return hmac.new(key or _PROCESS_ALIAS_KEY, f"{kind}\x00{value}".encode("utf-8"),
                    hashlib.sha256).hexdigest()[:_ALIAS_HEX]


def lo_alias(lo_id: str, key: bytes | None = None) -> str:
    """The opaque id that stands for a generated topic while its name is
    withheld: a keyed digest (HMAC-SHA256 with the vault's alias key), stable
    for one key, accepted back as a named id (:func:`resolve_scope`). An
    unkeyed digest of the id would let a client that guessed the title (the
    id's slug) confirm it."""

    return LO_ALIAS_PREFIX + _keyed(key, "learning_object", str(lo_id))


def group_alias(group_key: str, key: bytes | None = None) -> str:
    """A recurrence group's key as shown: a keyed digest of the stored key
    (itself a digest of the root's statement, which a client that guessed the
    statement could recompute: Q13)."""

    return GROUP_ALIAS_PREFIX + _keyed(key, "recurrence_group", str(group_key))


def _lowered(note: str) -> str:
    return note[:1].lower() + note[1:]


# -- the guard ------------------------------------------------------------------------


#: Gap sources whose words are an answer itself (``learner_text_gaps.source_kind``).
_ANSWER_SOURCES = frozenset({"diagnosis", "stuck_answer"})
_CHUNK = 500
#: The id the learner-text pipeline gives a prerequisite it creates
#: (``text_gaps.actions.creation_ids``: ``lo_ltg_<slug of its title>_<hash>``).
_GENERATED_LO_PREFIX = "lo_ltg_"
TITLE_LIMIT = 200
_ID_LIMIT = 512


class TextGuard:
    """THE renderer of every text the chat frontend shows (spec §4.7 rule 1).

    One rule: a text is released only as

    * (a) :meth:`_authored`: a topic's name or id that is not generated (the
      learner-text pipeline's prerequisites are: by their provenance, their
      id's form, or a gap recording their creation), and the question as
      graded (:meth:`stem`);
    * (b) :meth:`answer`: the learner's own answer, when the answer passes its
      protection (:meth:`attempt_reason`), the keys could be read and it
      reproduces none its item is known to have had, and it was graded against
      exactly one pinned contract on its own item;
    * (c) :meth:`derived`: anything else, only when its write-time record
      (:class:`WriteProvenance`) is complete and every input is safe: each
      answer passes (b)'s checks, each item its protection, each topic is
      authored, the protection and keys could be read, and the text
      reproduces no key of those items and topics. With no record (today,
      always) the text is withheld with :data:`HELD_BACK`.

    A generated topic's name is (c) text: while it is withheld the entry shows
    :data:`TOPIC_WITHHELD` and its id an opaque keyed alias (:func:`lo_alias`),
    and a topic search does not match its words.

    ``withheld`` and the key book are read when first needed (the ``today`` and
    ``progress`` views name topics only). Lookups are cached for one read;
    nothing is written."""

    def __init__(self, connection: Any, vault: Any, repository: Any = None, *, withheld: Withheld | None = None,
                 book: KeyBook | None = None, unknowns: list[str] | None = None, alias_key: bytes | None = None,
                 provenance: ProvenanceSource | None = None) -> None:
        self._connection = connection
        self._vault = vault
        self._repository = repository
        self._withheld = withheld
        self._book = book
        self._unknowns = unknowns if unknowns is not None else []
        self._key = alias_key
        self._provenance = provenance or no_write_provenance
        self._attempts: dict[str, dict[str, Any] | None] = {}
        self._pinned: dict[str, Any] = {}
        self._names: dict[str, tuple[GuardedText | None, str | None]] = {}
        self._generated: frozenset[str] | None = None

    @property
    def withheld(self) -> Withheld:
        if self._withheld is None:
            self._withheld = (withheld_items(self._vault, self._repository) if self._repository is not None
                              else Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,)))
            for unknown in self._withheld.unknowns:
                if unknown not in self._unknowns:
                    self._unknowns.append(unknown)
        return self._withheld

    @property
    def book(self) -> KeyBook:
        if self._book is None:
            self._book = key_book(self._connection, self._vault, self._unknowns)
        return self._book

    # -- (b) the learner's own answers -------------------------------------------------

    def _load(self, attempt_ids: Iterable[Any]) -> None:
        wanted = sorted(attempt for attempt in _ids(attempt_ids) if attempt not in self._attempts)
        if not wanted:
            return
        found: dict[str, dict[str, Any] | None] = dict.fromkeys(wanted)
        for start in range(0, len(wanted), _CHUNK):
            chunk = wanted[start:start + _CHUNK]
            for row in self._connection.execute(
                f"SELECT id, practice_item_id, attempt_type, probe_presentation_id, learning_object_id, "
                f"learner_answer_md FROM practice_attempts WHERE id IN ({_marks(chunk)})", chunk,
            ):
                found[str(row[0])] = {"item": None if row[1] is None else str(row[1]), "type": row[2],
                                      "probe": row[3], "lo": None if row[4] is None else str(row[4]),
                                      "answer": row[5]}
        self._attempts.update(found)
        self._pinned.update(_pins(self._connection, {attempt: row["item"] for attempt, row in found.items() if row},
                                  self._unknowns))

    def attempt_reason(self, attempt_id: Any) -> str | None:
        """Why this answer, and everything about it, is protected (the
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

    def answer(self, attempt_id: Any, text: Any, limit: int) -> tuple[AnswerText | None, str | None]:
        """(b) THE renderer of the learner's own answer: ``(text, None)``
        released, ``(None, why)``, or ``(None, None)`` for no text."""

        if text is None or not str(text).strip():
            return None, None
        reason = self.attempt_reason(attempt_id)
        if reason:
            return None, f"withheld: {reason}"
        if self.book.unreadable:
            return None, KEYS_UNREADABLE
        row = self._attempts[str(attempt_id)] or {}
        if leaks_key(str(text), self.book.item(row.get("item"))):
            return None, KEY_WITHHELD
        if str(attempt_id) not in self._pinned:
            return None, REVISION_UNKNOWN
        return AnswerText(excerpt(text, limit), _RELEASE), None

    def answer_of(self, attempt_id: Any, limit: int) -> tuple[AnswerText | None, str | None]:
        """The answer as the attempt records it (a gap drawn from an answer
        shows the answer itself, not the excerpt its reader chose)."""

        self._load([attempt_id])
        row = self._attempts.get(str(attempt_id))
        if row is None:
            return None, f"withheld: {ANSWER_UNRECORDED}"
        return self.answer(attempt_id, row["answer"], limit)

    # -- (a) authored vault text ---------------------------------------------------------

    def _authored(self, text: Any, limit: int) -> AuthoredText | None:
        if text is None or not str(text).strip():
            return None
        return AuthoredText(excerpt(text, limit), _RELEASE)

    def stem(self, attempt_id: Any, lo_id: Any) -> tuple[GuardedText | None, str | None]:
        """The question as graded: the prompt of the attempt's pinned
        contract. An item on a generated topic was seeded from the learner's
        question (``text_gaps.actions.seed_from_question``), so its prompt is
        drafted text: (c)."""

        prompt = self.pinned_prompt(attempt_id)
        if not prompt:
            return None, STEM_UNRECORDED
        row = self._attempts.get(str(attempt_id)) or {}
        item = (getattr(self._vault, "practice_items", None) or {}).get(str(row.get("item") or ""))
        topics = {str(lo) for lo in (lo_id, row.get("lo"), getattr(item, "learning_object_id", None)) if lo}
        if any(self.generated(lo) for lo in topics):
            return self.derived("practice_item", str(row.get("item") or ""), prompt, STEM_LIMIT,
                                answers=(attempt_id,), items=(row.get("item"),), los=topics)
        return self._authored(prompt, STEM_LIMIT), None

    # -- (c) derived text, by its write-time record --------------------------------------

    def derived(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any] = (),
                items: Iterable[Any] = (), los: Iterable[Any] = ()) -> tuple[RecordedText | None, str | None]:
        """(c) THE renderer of a derived text: released only by a complete
        write-time record whose inputs, with the entry's own ``answers``,
        ``items`` and ``los``, are all safe. ``text`` may be a function, called
        only once the record passes. Without a record: ``(None, HELD_BACK)``."""

        if not callable(text) and (text is None or not str(text).strip()):
            return None, None
        # The entry's own answers and items first: a protected one is named as
        # such (a check waiting in the app), whatever any record says.
        reason = self._protected(sorted(_ids(answers)), sorted(_ids(items)))
        if reason:
            return None, reason
        try:
            record = self._provenance(self._connection, kind, str(record_id or ""))
        except Exception:  # noqa: BLE001 - fail closed: an unreadable record is no record
            _LOG.warning("learner context: write-time provenance not read (%s)", kind, exc_info=True)
            record = None
        if not isinstance(record, WriteProvenance) or not record.readable():
            return None, HELD_BACK
        answer_ids = sorted(_ids(record.answers) | _ids(answers))
        item_ids = sorted(_ids(record.items) | _ids(items))
        reason = self._unsafe(record, answer_ids, item_ids)
        if reason:
            return None, reason
        value = text() if callable(text) else text
        if value is None or not str(value).strip():
            return None, None
        rows = [row for answer in answer_ids if (row := self._attempts.get(answer))]
        keys = [key for item in sorted(set(item_ids) | {row["item"] for row in rows if row["item"]})
                for key in self.book.item(item)]
        keys += self.book.los(sorted(_ids(record.topics) | _ids(los)))
        if leaks_key(str(value), keys):
            return None, KEY_WITHHELD
        return RecordedText(excerpt(value, limit), _RELEASE), None

    def _protected(self, answers: Sequence[str], items: Sequence[str]) -> str | None:
        """Why any of these answers or items is protected (or protection is
        unreadable), or None."""

        if not (answers or items):
            return None
        if not self.withheld.available:
            return f"withheld: {WITHHELD_UNREADABLE}"
        self._load(answers)
        for answer in answers:
            reason = self.attempt_reason(answer)
            if reason:
                return f"withheld: {reason}"
        for item in items:
            reason = self.withheld.reason(item)
            if reason:
                return f"withheld: {reason}"
        return None

    def _unsafe(self, record: WriteProvenance, answers: Sequence[str], items: Sequence[str]) -> str | None:
        """Why a record's inputs (with the entry's own) are not all safe, or None."""

        if not self.withheld.available:
            return f"withheld: {WITHHELD_UNREADABLE}"
        reason = self._protected(answers, items)
        if reason:
            return reason
        los = getattr(self._vault, "learning_objects", None) or {}
        if any(topic not in los or self.generated(topic) for topic in record.topics):
            return HELD_BACK
        if self.book.unreadable:
            return KEYS_UNREADABLE
        if any(answer not in self._pinned for answer in answers):
            return REVISION_UNKNOWN_BEHIND
        return None

    # -- topic names and ids -------------------------------------------------------------

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
            if _table(self._connection, "learner_text_gaps"):
                for created, target in self._connection.execute(
                    "SELECT created_learning_object_id, CASE WHEN action = 'created_prerequisite' AND "
                    "target_kind = 'learning_object' THEN target_id END FROM learner_text_gaps "
                    "WHERE created_learning_object_id IS NOT NULL OR action = 'created_prerequisite'"
                ):
                    found |= {str(value) for value in (created, target) if value}
            self._generated = frozenset(found)
        return self._generated

    def generated(self, lo_id: Any) -> bool:
        key = str(lo_id or "")
        return bool(key) and (key.startswith(_GENERATED_LO_PREFIX) or key in self._generated_ids())

    def _name(self, lo_id: str) -> tuple[GuardedText | None, str | None]:
        """A topic's name released, or why not. A generated topic's title (or,
        when it has left the vault, its id) is drafted text; its id carries a
        slug of that title, so the id's words pass the same check."""

        if lo_id not in self._names:
            lo = self._lo(lo_id)
            title = lo.title if lo is not None and str(lo.title or "").strip() else lo_id
            if not self.generated(lo_id):
                self._names[lo_id] = (self._authored(title, TITLE_LIMIT), None)
            else:
                shown, note = self.derived("learning_object", lo_id, title, TITLE_LIMIT, los=(lo_id,))
                if shown is not None:
                    words, note = self.derived("learning_object", lo_id, lo_id.replace("_", " "), _ID_LIMIT,
                                               los=(lo_id,))
                    shown = shown if words is not None else None
                self._names[lo_id] = (shown, note)
        return self._names[lo_id]

    def topic(self, lo_id: Any) -> str | None:
        """THE renderer of a topic's name: released, or
        :data:`TOPIC_WITHHELD` and why."""

        if not lo_id:
            return None
        shown, note = self._name(str(lo_id))
        return shown if shown is not None else f"{TOPIC_WITHHELD} ({_lowered(note or HELD_BACK)})"

    def lo_ref(self, lo_id: Any) -> str | None:
        """THE renderer of a topic's id: released, or an opaque keyed alias
        (:func:`lo_alias`) while a generated topic's name is withheld."""

        if not lo_id:
            return None
        key = str(lo_id)
        if not self.generated(key):
            return self._authored(key, _ID_LIMIT)
        if self._name(key)[0] is None:
            return lo_alias(key, self._key)
        return self.derived("learning_object", key, key, _ID_LIMIT, los=(key,))[0]

    def aliases(self) -> dict[str, str]:
        """``{alias: topic id}`` for every generated topic (a named id the
        frontend may send back)."""

        return {lo_alias(lo_id, self._key): lo_id for lo_id in self._generated_ids()}

    def searchable(self, lo_id: Any) -> bool:
        """Whether a topic search may match this topic's words: not while a
        generated name is withheld (the match would confirm its words)."""

        return not self.generated(lo_id) or self._name(str(lo_id))[0] is not None

    def group_ref(self, group_key: Any) -> str:
        """A recurrence group's key as shown (:func:`group_alias`)."""

        return group_alias(str(group_key), self._key)


# -- the output's text fields, each classified ----------------------------------------
#
# Paths: ``section[].field``, ``[]`` for a list, a union entry by its kind
# (``open_hypotheses[diagnosed_cause].statement``). A test checks these against
# the output schema (``ContextOut`` in ``learnloop_mcp.server``) and against
# the values each field holds.

#: The rules, by the type each releases.
AUTHORED, ANSWER, RECORDED = "authored", "answer", "recorded"
RELEASE_TYPES: Mapping[str, type[GuardedText]] = {AUTHORED: AuthoredText, ANSWER: AnswerText,
                                                  RECORDED: RecordedText}

#: Every topic name: (a) the vault's title, or a generated topic's drafted
#: one ((c); while withheld, :data:`TOPIC_WITHHELD` and why).
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
#: Every topic id: (a), or a generated topic's ((c); while withheld, an
#: opaque :data:`LO_ALIAS_PREFIX` alias).
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
#: Texts a model wrote, or that were derived from what one wrote: (c) only.
DERIVED_FIELDS: frozenset[str] = frozenset({
    "misconceptions[].statement",
    "misconceptions[].correction",
    "misconception_candidates[].statement",
    "open_hypotheses[diagnosed_cause].statement",
    "recurrence_groups[].statement",
    "recent_answer_traces[].diagnosis.summary",
    "recent_answer_traces[].diagnosis.hypotheses[]",
    "open_learner_text_gaps[].target",
})
#: Every text field that carries content, and the rules that may release it.
RELEASED_BY: Mapping[str, frozenset[str]] = {
    **{path: frozenset({AUTHORED, RECORDED}) for path in TOPIC_FIELDS | TOPIC_ID_FIELDS},
    "recent_answer_traces[].stem": frozenset({AUTHORED, RECORDED}),
    "recent_answer_traces[].answer": frozenset({ANSWER}),
    # A gap's words: the pinned answer they are (b), or a question asked (c).
    "open_learner_text_gaps[].learner_text": frozenset({ANSWER, RECORDED}),
    **{path: frozenset({RECORDED}) for path in DERIVED_FIELDS},
}
_ID, _TIME, _ENUM, _NOTE = ("a record id (a ULID; a group key is a keyed digest)", "a timestamp",
                            "a stored code (an enumeration)", "a fixed note")
#: Every other text field: structure, never content, and why.
STRUCTURAL_FIELDS: Mapping[str, str] = {
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

    ``aliases`` (:meth:`TextGuard.aliases`) resolve the opaque id a generated
    topic is shown under while its name is withheld; ``searchable``
    (:meth:`TextGuard.searchable`) keeps a topic search from matching the
    words of a withheld name (a match would confirm them)."""

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


def _misconceptions(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
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
                lo_id = values["learning_object_id"]
                statement, note = guard.derived("misconception", values["id"], values["statement"],
                                                STATEMENT_LIMIT, los=(lo_id,))
                correction, correction_note = guard.derived("misconception_correction", values["id"],
                                                            values.get("correction_statement"), STATEMENT_LIMIT,
                                                            los=(lo_id,))
                sightings = _loads(values["source_error_event_ids_json"], [])
                registry.append({
                    "misconception_id": values["id"],
                    "learning_object_id": guard.lo_ref(lo_id),
                    "topic": guard.topic(lo_id),
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
                lo_id = values["learning_object_id"]
                statement, note = guard.derived("candidate", values["id"], values["statement"], STATEMENT_LIMIT,
                                                los=(lo_id,))
                candidates.append({
                    "candidate_id": values["id"],
                    "learning_object_id": guard.lo_ref(lo_id),
                    "topic": guard.topic(lo_id),
                    "status": "candidate", "statement": statement, "statement_note": note,
                    "evidence_count": int(values["occurrence_count"] or 0),
                    "note": "held until it recurs; not yet a recorded misconception",
                    "since": values["created_at"], "updated_at": values["updated_at"],
                })
    except Exception:  # noqa: BLE001 - named as unknown
        _LOG.warning("learner context: misconceptions not read", exc_info=True)
        unknowns.append("misconceptions could not be read")
    return registry[: limits.misconceptions], candidates[: limits.candidates]


def _hypotheses(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
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


def _diagnosed_causes(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
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
            statement, note = guard.derived("hypothesis", row["id"], row["statement"], STATEMENT_LIMIT,
                                            answers=episode_attempts | _ids([row["attempt_id"]]),
                                            los=(row["learning_object_id"],))
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


def _unresolved_causes(connection: Any, los: set[str], guard: TextGuard,
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


def _recurrence_groups(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
                       unknowns: list[str]) -> list[dict[str, Any]]:
    """Groups touching the scope's LOs. An empty scope has none (a topic or
    ids that matched nothing is not a whole-learner request: that scope is
    every active LO). A group's statement is its root's (a hypothesis
    statement, (c)); every answer of every member episode is checked with it.
    Its key is a keyed digest (Q13)."""

    groups: list[dict[str, Any]] = []
    if not los:
        return groups
    try:
        if not (_table(connection, "hypothesis_recurrence_groups") and _table(connection, "causal_hypotheses")):
            return groups
        members: dict[str, list[dict[str, Any]]] = {}
        for row in connection.execute(
            """SELECT g.group_key, g.episode_key, g.root_episode_key, g.class_count, g.joined_by,
                      h.id AS hypothesis_id, h.learning_object_id, h.statement
                 FROM hypothesis_recurrence_groups g
                 JOIN causal_hypotheses h ON h.episode_key = g.episode_key
                  AND h.version = (SELECT MAX(v.version) FROM causal_hypotheses v WHERE v.episode_key = g.episode_key)
                ORDER BY g.group_key, g.episode_key"""
        ):
            members.setdefault(str(row["group_key"]), []).append(dict(row))
        selected = {key: rows for key, rows in members.items()
                    if {str(row["learning_object_id"]) for row in rows} & los}
        episodes = sorted({str(row["episode_key"]) for rows in selected.values() for row in rows})
        answers: dict[str, set[str]] = {}
        for start in range(0, len(episodes), _CHUNK):
            chunk = episodes[start:start + _CHUNK]
            for episode, attempt in connection.execute(
                f"SELECT episode_key, attempt_id FROM causal_hypotheses WHERE episode_key IN ({_marks(chunk)})", chunk,
            ):
                if attempt:
                    answers.setdefault(str(episode), set()).add(str(attempt))
        for group_key, rows in selected.items():
            lo_ids = sorted({str(row["learning_object_id"]) for row in rows})
            root = next((row for row in rows if row["episode_key"] == row["root_episode_key"]), rows[0])
            behind = {attempt for row in rows for attempt in answers.get(str(row["episode_key"]), ())}
            statement, note = guard.derived("hypothesis", root["hypothesis_id"], root["statement"], STATEMENT_LIMIT,
                                            answers=behind, los=lo_ids)
            groups.append({
                "group_key": guard.group_ref(group_key), "statement": statement, "statement_note": note,
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


def _traces(connection: Any, repository: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
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
        lo_id = row["learning_object_id"]
        # The answers' protection check; the answer itself is (b), the
        # question as graded (a), the diagnosis (c).
        reason = guard.attempt_reason(attempt_id)
        answer = answer_note = stem = stem_note = None
        if reason is None:
            answer, answer_note = guard.answer(attempt_id, row.get("learner_answer_md"), EXCERPT_LIMIT)
            stem, stem_note = guard.stem(attempt_id, lo_id)
        diagnosis = _diagnosis(repository, guard, attempt_id, lo_id, row.get("practice_item_id"),
                               hidden=reason is not None, hypotheses=hypotheses.get(attempt_id, []))
        status = row.get("reference_status")
        traces.append({
            "attempt_id": attempt_id, "at": row["created_at"],
            "learning_object_id": guard.lo_ref(lo_id),
            "topic": guard.topic(lo_id),
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
            "stem": stem, "stem_note": stem_note,
            "answer": answer, "answer_note": answer_note,
            "diagnosis": diagnosis,
        })
    return traces


def _diagnosis(repository: Any, guard: TextGuard, attempt_id: str, lo_id: Any, item_id: Any, *, hidden: bool,
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
        if analysis.strip():
            summary, note = guard.derived("diagnosis", diagnosis_id, lambda: plain_summary(repository, analysis),
                                          STATEMENT_LIMIT, answers=(attempt_id,), items=(item_id,), los=(lo_id,))
            if note:
                entry["summary_note"] = note
    entry["summary"] = summary
    rendered = [guard.derived("hypothesis", row["id"], row["statement"], STATEMENT_LIMIT, answers=(attempt_id,),
                              los=(row["learning_object_id"],)) for row in hypotheses]
    entry["hypotheses"] = [text for text, _note in rendered if text]
    notes = [note for _text, note in rendered if note]
    if notes:
        entry["hypotheses_note"] = notes[0]
    return entry


def _gaps(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard,
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
            text, note = _gap_words(guard, values)
            target, target_note, target_topic = _gap_target(connection, guard, values["target_kind"],
                                                            values["target_id"])
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


def _gap_words(guard: TextGuard, row: Mapping[str, Any]) -> tuple[GuardedText | None, str | None]:
    """A gap's words: the pinned answer they are (a diagnosis's or a stuck
    answer's gap: (b), shown as the attempt records it), else a question the
    learner asked ((c): what it was asked about is not recorded with it, Q10)."""

    attempt_id = row.get("attempt_id")
    if row.get("source_kind") in _ANSWER_SOURCES and attempt_id:
        return guard.answer_of(attempt_id, STATEMENT_LIMIT)
    return guard.derived("learner_text_gap", row.get("id"), row.get("learner_text"), STATEMENT_LIMIT,
                         answers=_ids([attempt_id]), items=_ids([row.get("practice_item_id")]),
                         los=_ids([row.get("anchor_learning_object_id")]))


def _belief(connection: Any, kind: str, record_id: Any) -> tuple[str, Any, Any] | None:
    """``(record kind, statement, topic)`` of the belief a gap was matched to:
    a recorded misconception (``durable``), or a candidate in the holding pen
    or the hypothesis it projects (``candidate``). None when not on record."""

    tables = {"durable": (("misconception", "misconceptions"),),
              "candidate": (("candidate", "misconception_candidates"), ("hypothesis", "causal_hypotheses"))}
    for record_kind, table in tables.get(kind, ()):
        if _table(connection, table):
            row = connection.execute(f"SELECT statement, learning_object_id FROM {table} WHERE id = ?",
                                     (str(record_id),)).fetchone()
            if row is not None:
                return record_kind, row[0], row[1]
    return None


def _gap_target(connection: Any, guard: TextGuard, kind: Any,
                target_id: Any) -> tuple[GuardedText | None, str | None, str | None]:
    """What a gap was matched to: ``(statement, note, topic)``. A topic is its
    name (:meth:`TextGuard.topic`: a prerequisite the gap created was named
    from the learner's text); a recorded misconception or a candidate is a
    statement a model wrote, (c)."""

    if not kind or not target_id:
        return None, None, None
    if kind == "learning_object":
        return None, None, guard.topic(target_id)
    found = _belief(connection, str(kind), target_id)
    if found is None:
        return None, "the belief it was matched to is not on record", None
    record_kind, statement, lo_id = found
    shown, note = guard.derived(record_kind, target_id, statement, STATEMENT_LIMIT, los=(lo_id,))
    return shown, note, guard.topic(lo_id)


def retention_risks(vault: Any, repository: Any, los: Iterable[str], *, now: datetime, limit: int = 15,
                    unknowns: list[str] | None = None, topic: Callable[[str], Any] | None = None,
                    ref: Callable[[str], Any] | None = None) -> list[dict[str, Any]]:
    """Topics whose modelled recall now is below :data:`RETENTION_TARGET`, or due now.

    FSRS retrievability from each item's stored memory state: a model
    estimate, not a test. Lowest recall first. ``topic`` and ``ref`` name a
    topic in the output (the chat frontend passes its guard's
    :meth:`TextGuard.topic` and :meth:`TextGuard.lo_ref`); by default the
    vault's title and id."""

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
    alias_key: bytes | None = None,
    provenance: ProvenanceSource | None = None,
) -> dict[str, Any]:
    """The shared latent-state read model for one scope. Read-only.

    ``alias_key`` keys the opaque aliases (the server passes the vault's,
    ``RemoteRuntime.alias_key``; else this process's). ``provenance`` is where
    write-time records are read from (rule (c)); none records one yet."""

    limits = limits or ContextLimits()
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    now_iso = moment.strftime("%Y-%m-%dT%H:%M:%SZ") if now is not None else utc_now_iso()
    unknowns: list[str] = []
    withheld = withheld if withheld is not None else withheld_items(vault, repository)
    unknowns.extend(withheld.unknowns)
    with repository.connection() as connection:
        # Every text below, every topic name and id included, is released by this one guard.
        guard = TextGuard(connection, vault, repository, withheld=withheld,
                          book=key_book(connection, vault, unknowns), unknowns=unknowns, alias_key=alias_key,
                          provenance=provenance)
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
    "ANSWER",
    "AUTHORED",
    "CONTEXT_VERSION",
    "DERIVED_FIELDS",
    "DERIVED_KINDS",
    "GROUP_ALIAS_PREFIX",
    "HELD_BACK",
    "KEY_WITHHELD",
    "LO_ALIAS_PREFIX",
    "PROTECTION_UNKNOWN",
    "RECORDED",
    "RELEASED_BY",
    "RELEASE_TYPES",
    "RETENTION_TARGET",
    "SNAPSHOT_UNSETTLED",
    "STRUCTURAL_FIELDS",
    "TOPIC_FIELDS",
    "TOPIC_ID_FIELDS",
    "TOPIC_WITHHELD",
    "WITHHELD_UNKNOWN_ITEM",
    "WITHHELD_UNREADABLE",
    "AnswerText",
    "AuthoredText",
    "ContextLimits",
    "GuardedText",
    "KeyBook",
    "ProvenanceSource",
    "RecordedText",
    "TextGuard",
    "Withheld",
    "WriteProvenance",
    "excerpt",
    "group_alias",
    "key_book",
    "leaks_key",
    "learning_context",
    "lo_alias",
    "no_write_provenance",
    "protection_issues",
    "resolve_scope",
    "retention_risks",
    "withheld_items",
]
