"""What of the learner's past work a model context may show: one authority.

Two readers put the learner's past work in front of a model, and both read
it through this module:

* router R2a's ``LearnerStateCardV1`` (``daily_plan.router_card``): the router
  models read it, and R2c's teach-back summaries are made and read under it;
* the chat frontend's read model (``learner_context``): a chat host reads it.

They share every predicate and every protection here, and keep apart only
their **text rule** (:class:`TextRule`, a parameter of :func:`past_work_text`
and :func:`statement_text`). The card's reader is the router model, so its
rule is plan §3.6's gate G5 (``router_card.CardText``: the learner's own
answers and the statements LearnLoop's diagnosers wrote are shown).
The chat's reader is a chat host, so its rule is ``learner_context.TextGuard``
(authored vault text, the learner's own pinned answers and, once recorded,
text with a safe write-time provenance; everything a model wrote is held
back). Convergence at the chat frontend's landing (docs/reviews/mcp-c1a.md,
Q16): the predicates and the protection shared, each text rule kept.

**The protection:**

* **Withheld items** (:func:`withheld_items`): exam and held-out material by
  the one exam predicate (``content.sources.exam_material``: exam members and
  units, held-out units, the unreleased exam pools, and items whose own source
  is any of them, by ``item_exam_status``), live assessment reservations,
  items an open cold check or a repair's cold retry holds, and diagnostic
  probes. An item the vault cannot read (deleted, or its file unreadable) is
  withheld too, since it cannot be checked. When any predicate fails, or the
  protection metadata cannot be trusted (:func:`protection_issues`), nothing
  shows (fail closed). Not behind ``goals.held_out_selection``: that switch
  restores the predecessor's *serving* selection, and a model context's
  protections are never switched.
* **An attempt's own protection** (:func:`attempt_protection`): its item's,
  exam work (``exam_attempt``, ``exam_evidence``) and a diagnostic probe. A
  protected attempt keeps its result and shows no question and no answer.
* **Held grades:** THE predicate (``learnloop.held_grades``); a held grade is
  "held for review", never a score (:func:`attempt_result`).
* **Pinned revisions** (:func:`pinned_contracts`): the question an answer was
  graded against is the prompt of the one assessment contract its live
  grading evidence names, on the attempt's own item (router R2a review F6),
  rendered with the required method that contract froze (method-explicit
  items: :meth:`PinnedContract.question`). Today's edited prompt is never
  substituted; an attempt whose revision cannot be established shows no
  question.
* **Leakage of derived text** (:meth:`PastWork.evidence_reason`): a statement
  written from protected work (a cause diagnosed from an exam answer, a
  learner's words about a probe) keeps its entry and never its words.

Only the prompt and the required method of a contract are read here, never
an answer key, a reference solution or a rubric. Read-only; nothing is
written and no model is called.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

_LOG = logging.getLogger(__name__)

#: Why an item's (or an attempt's) question and answers are withheld.
WITHHELD_EXAM = "exam or held-out material"
WITHHELD_RESERVED = "reserved for an assessment"
WITHHELD_COLD = "a check waiting in the app"
WITHHELD_PROBE = "a diagnostic check"
WITHHELD_UNREADABLE = "the protection rules could not be read"
WITHHELD_UNKNOWN_ITEM = "its question could not be checked (not readable in the vault)"
#: An attempt a text names that is not on record.
ANSWER_UNRECORDED = "an answer it was drawn from is not on record"
#: A shown attempt with no established question revision.
STEM_UNRECORDED = "question revision not recorded"
PINS_UNREADABLE = ("the question revisions past answers were graded against could not be read: no question or "
                   "answer is shown")
#: A loader issue the remote runtime adds when the vault's files changed while
#: it read them, or a protection-bearing file was caught mid-write (empty):
#: nothing read from that snapshot can say what is protected.
SNAPSHOT_UNSETTLED = "vault:snapshot_unsettled"
PROTECTION_UNKNOWN = "which material is protected could not be read: no question or answer is shown"

EXAM_ATTEMPT_TYPES = frozenset({"exam_attempt", "exam_evidence"})
PROBE_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe"})
COLD_TASK_KINDS = ("cold_retry", "certification_cold_probe")
_CHUNK = 500


def _table(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def _ids(values: Iterable[Any]) -> frozenset[str]:
    return frozenset(str(value) for value in values if value)


# -- withheld items -------------------------------------------------------------------


@dataclass(frozen=True)
class Withheld:
    """Items whose question and answers never reach a model context, and why.

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
    """Every item whose question and answers a model context never shows.

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
        _LOG.warning("learner protection: protection metadata not trusted: %s", "; ".join(problems))
        return Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,))
    try:
        from learnloop.content.sources import exam_material as EM

        reserved = frozenset(str(item_id) for item_id in repository.reserved_exam_pool_item_ids())
        for item_id in reserved:
            reasons.setdefault(item_id, WITHHELD_EXAM)
        for item_id in EM.held_out_items(vault, repository):
            reasons.setdefault(str(item_id), WITHHELD_EXAM)
        exam = EM.exam_material(vault, repository)
        for item in vault.practice_items.values():
            if EM.item_exam_status(item, material=exam, reserved=reserved) is not None:
                reasons.setdefault(item.id, WITHHELD_EXAM)
        for row in repository.reserved_assessment_surfaces():
            legacy = row.get("legacy_practice_item_id")
            if legacy:
                reasons.setdefault(str(legacy), WITHHELD_RESERVED)
        for kind in COLD_TASK_KINDS:
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
            if item.practice_mode in PROBE_MODES:
                reasons.setdefault(item.id, WITHHELD_PROBE)
    except Exception:  # noqa: BLE001 - fail closed: nothing shows
        _LOG.warning("learner protection: protection predicates not read", exc_info=True)
        return Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,))
    return Withheld(reasons=reasons, known_items=frozenset(str(item_id) for item_id in vault.practice_items))


def attempt_protection(withheld: Withheld, attempt: Mapping[str, Any] | None) -> str | None:
    """Why an attempt's question and answer are withheld, or None.

    ``attempt`` is ``{"item", "type", "probe"}`` (its practice item, attempt
    type and probe presentation), or None when it is not on record. Its
    item's protection first, then exam work and a diagnostic probe."""

    if not withheld.available:
        return WITHHELD_UNREADABLE
    if attempt is None:
        return ANSWER_UNRECORDED
    if not attempt.get("item"):
        return WITHHELD_UNKNOWN_ITEM
    reason = withheld.reason(attempt["item"])
    if reason:
        return reason
    if attempt.get("type") in EXAM_ATTEMPT_TYPES:
        return WITHHELD_EXAM
    if attempt.get("type") == "diagnostic_probe" or attempt.get("probe"):
        return WITHHELD_PROBE
    return None


# -- held grades ---------------------------------------------------------------------


def attempt_result(correctness: Any, held: bool) -> str:
    """An attempt's result class: a grade held for review (THE predicate,
    ``held_grades``) is ``held_for_review``, never a score."""

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


def held_attempts(connection: Any, attempt_ids: Sequence[Any]) -> frozenset[str]:
    """The attempts among ``attempt_ids`` whose grade is held for review (THE predicate)."""

    from learnloop import held_grades

    ids = [str(attempt_id) for attempt_id in attempt_ids if attempt_id]
    return held_grades.held_for_review_attempts(connection, ids) if ids else frozenset()


# -- pinned revisions ----------------------------------------------------------------


def frozen_method(value: Any) -> Any:
    """A contract's frozen ``required_method`` as ``json_extract`` returns it
    (a JSON text for an object), or None."""

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    return value if isinstance(value, Mapping) else None


@dataclass(frozen=True)
class PinnedContract:
    """The assessment contract an answer was graded against: its statement and
    the required method it froze. Never its key or rubric."""

    contract_id: str
    item_id: str
    prompt: str | None
    required_method: Mapping[str, Any] | None = None

    def question(self, limit: int, clip: Callable[[str, int], str]) -> str | None:
        """The question as graded, or None without a statement: the frozen
        statement, then the instruction of the method it froze, the statement
        shortened by ``clip`` so the instruction stays whole within ``limit``
        (``vault.required_method.fit_presented_prompt``, the contract's pair
        ``answered_question`` renders for a method-explicit answer). Without a
        frozen method it is the statement as frozen, for the reader's own
        clip: never today's prompt, whatever the item says now."""

        from learnloop.vault.required_method import fit_presented_prompt, method_instruction

        if not (isinstance(self.prompt, str) and self.prompt.strip()):
            return None
        if method_instruction(self.required_method) is None:
            return self.prompt
        return fit_presented_prompt(self.prompt, self.required_method, limit, clip)


def pinned_contracts(connection: Any, items: Mapping[str, Any]) -> dict[str, PinnedContract]:
    """``{attempt id: its pinned contract}`` for the attempts (``{attempt id:
    practice item}``) graded against exactly one assessment contract of their
    own item: the only affirmative record of the question revision an answer
    was graded against (router R2a review F6). Only the prompt and the frozen
    required method are read (``json_extract``). Raises when they cannot be
    read; the caller names that and pins nothing."""

    ids = [str(attempt_id) for attempt_id in items if attempt_id]
    if not ids:
        return {}
    if not _table(connection, "assessment_contract_versions") or not _table(connection, "grading_evidence"):
        return {}
    contracts: dict[str, set[Any]] = {}
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        for attempt_id, contract_id in connection.execute(
            f"SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
            f"WHERE superseded_at IS NULL AND attempt_id IN ({_marks(chunk)})", chunk,
        ):
            contracts.setdefault(str(attempt_id), set()).add(contract_id)
    single = {attempt: next(iter(found)) for attempt, found in contracts.items()
              if len(found) == 1 and None not in found}
    versions = sorted({str(value) for value in single.values()})
    rows: dict[str, tuple[Any, Any, Any]] = {}
    for start in range(0, len(versions), _CHUNK):
        chunk = versions[start:start + _CHUNK]
        for row in connection.execute(
            f"SELECT id, practice_item_id, json_extract(contract_json, '$.prompt'), "
            f"json_extract(contract_json, '$.required_method') "
            f"FROM assessment_contract_versions WHERE id IN ({_marks(chunk)})", chunk,
        ):
            rows[str(row[0])] = (row[1], row[2], row[3])
    pinned: dict[str, PinnedContract] = {}
    for attempt_id, version_id in single.items():
        item_id, prompt, method = rows.get(str(version_id), (None, None, None))
        if item_id is not None and str(item_id) == str(items.get(attempt_id) or ""):
            pinned[attempt_id] = PinnedContract(str(version_id), str(item_id),
                                                prompt if isinstance(prompt, str) else None, frozen_method(method))
    return pinned


def hypothesis_answers(connection: Any, hypothesis_ids: Iterable[Any]) -> dict[str, frozenset[str]]:
    """``{hypothesis id: the answers its episode rests on}``: the attempt of
    every version of the hypothesis's episode. A statement written for the
    episode is checked against all of them (:meth:`PastWork.evidence_reason`)."""

    ids = sorted(_ids(hypothesis_ids))
    if not ids or not _table(connection, "causal_hypotheses"):
        return {}
    episodes: dict[str, str] = {}
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        for row in connection.execute(
            f"SELECT id, episode_key FROM causal_hypotheses WHERE id IN ({_marks(chunk)})", chunk,
        ):
            episodes[str(row[0])] = str(row[1])
    keys = sorted(set(episodes.values()))
    attempts: dict[str, set[str]] = {}
    for start in range(0, len(keys), _CHUNK):
        chunk = keys[start:start + _CHUNK]
        for episode, attempt in connection.execute(
            f"SELECT episode_key, attempt_id FROM causal_hypotheses WHERE episode_key IN ({_marks(chunk)})", chunk,
        ):
            if attempt:
                attempts.setdefault(str(episode), set()).add(str(attempt))
    return {hypothesis: frozenset(attempts.get(episode, ())) for hypothesis, episode in episodes.items()}


# -- one read ------------------------------------------------------------------------


class PastWork:
    """One read's protection, cached: the withheld items, the attempts read,
    their pinned contracts. Every reader's protection is asked here.

    ``withheld`` is read when first needed (a reader that names topics only
    never reads it); without a repository the predicates cannot be read and
    nothing shows. Unknowns (unreadable protection or pins) are appended to
    ``unknowns``, once each."""

    def __init__(self, connection: Any, vault: Any, repository: Any = None, *, withheld: Withheld | None = None,
                 unknowns: list[str] | None = None) -> None:
        self.connection = connection
        self.vault = vault
        self.repository = repository
        self.unknowns = unknowns if unknowns is not None else []
        self._withheld = withheld
        self._attempts: dict[str, dict[str, Any] | None] = {}
        self._pinned: dict[str, PinnedContract] = {}

    def _note(self, unknown: str) -> None:
        if unknown not in self.unknowns:
            self.unknowns.append(unknown)

    @property
    def withheld(self) -> Withheld:
        if self._withheld is None:
            self._withheld = (withheld_items(self.vault, self.repository) if self.repository is not None
                              else Withheld(available=False, unknowns=(PROTECTION_UNKNOWN,)))
            for unknown in self._withheld.unknowns:
                self._note(unknown)
        return self._withheld

    def load(self, attempt_ids: Iterable[Any]) -> None:
        """Read these attempts (item, type, probe, topic, answer) and their pins."""

        wanted = sorted(attempt for attempt in _ids(attempt_ids) if attempt not in self._attempts)
        if not wanted:
            return
        found: dict[str, dict[str, Any] | None] = dict.fromkeys(wanted)
        for start in range(0, len(wanted), _CHUNK):
            chunk = wanted[start:start + _CHUNK]
            for row in self.connection.execute(
                f"SELECT id, practice_item_id, attempt_type, probe_presentation_id, learning_object_id, "
                f"learner_answer_md FROM practice_attempts WHERE id IN ({_marks(chunk)})", chunk,
            ):
                found[str(row[0])] = {"item": None if row[1] is None else str(row[1]), "type": row[2],
                                      "probe": row[3], "lo": None if row[4] is None else str(row[4]),
                                      "answer": row[5]}
        self._attempts.update(found)
        try:
            self._pinned.update(pinned_contracts(
                self.connection, {attempt: row["item"] for attempt, row in found.items() if row}))
        except Exception:  # noqa: BLE001 - named as unknown; no question shows
            _LOG.warning("learner protection: pinned contracts not read", exc_info=True)
            self._note(PINS_UNREADABLE)

    def attempt(self, attempt_id: Any) -> dict[str, Any] | None:
        """The attempt as read (``item``, ``type``, ``probe``, ``lo``, ``answer``), or None."""

        self.load([attempt_id])
        return self._attempts.get(str(attempt_id))

    def attempt_reason(self, attempt_id: Any) -> str | None:
        """Why this attempt's question and answer, and everything written
        about it, are protected (:func:`attempt_protection`), or None."""

        if not self.withheld.available:
            return WITHHELD_UNREADABLE
        return attempt_protection(self.withheld, self.attempt(attempt_id))

    def pinned(self, attempt_id: Any) -> PinnedContract | None:
        """The contract this answer was graded against, or None when the
        revision is not established (no contract, several, another item's)."""

        self.load([attempt_id])
        return self._pinned.get(str(attempt_id))

    def held(self, attempt_ids: Sequence[Any]) -> frozenset[str]:
        """The attempts whose grade is held for review (THE predicate)."""

        return held_attempts(self.connection, attempt_ids)

    def evidence_reason(self, answers: Iterable[Any] = (), items: Iterable[Any] = ()) -> str | None:
        """The leakage rule for a text written from these answers and items:
        why any of them is protected (or protection is unreadable), or None."""

        answer_ids, item_ids = sorted(_ids(answers)), sorted(_ids(items))
        if not (answer_ids or item_ids):
            return None
        if not self.withheld.available:
            return WITHHELD_UNREADABLE
        self.load(answer_ids)
        for answer in answer_ids:
            reason = self.attempt_reason(answer)
            if reason:
                return reason
        for item in item_ids:
            reason = self.withheld.reason(item)
            if reason:
                return reason
        return None


# -- the text rule, a parameter --------------------------------------------------------


class TextRule(Protocol):
    """How a reader's text leaves LearnLoop once the protection here has passed.

    Each returns ``(text, note)``: the text released, or None and why (a
    note), or ``(None, None)`` for no text. The card's G5 rule is
    ``daily_plan.router_card.CardText``; the chat's is
    ``learner_context.TextGuard``."""

    def question(self, attempt_id: str, lo_id: Any) -> tuple[str | None, str | None]:
        """The question an unprotected attempt was graded against."""

    def answer(self, attempt_id: str, text: Any, limit: int) -> tuple[str | None, str | None]:
        """The learner's own answer on an unprotected attempt."""

    def statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any] = (),
                  items: Iterable[Any] = (), los: Iterable[Any] = ()) -> tuple[str | None, str | None]:
        """A statement (a diagnosis's, a hypothesis's, a learner-text gap's
        words) whose answers and items are unprotected."""


@dataclass(frozen=True)
class PastWorkText:
    """What one past attempt shows: ``withheld`` (why its question and answer
    are protected) or its question and answer as the text rule released them."""

    withheld: str | None = None
    stem: str | None = None
    stem_note: str | None = None
    answer: str | None = None
    answer_note: str | None = None


def past_work_text(past: PastWork, rule: TextRule, attempt_id: Any, lo_id: Any, answer: Any,
                   answer_limit: int) -> PastWorkText:
    """One past attempt's question and answer: the protection, then the reader's text rule."""

    reason = past.attempt_reason(attempt_id)
    if reason:
        return PastWorkText(withheld=reason)
    stem, stem_note = rule.question(str(attempt_id), lo_id)
    shown, answer_note = rule.answer(str(attempt_id), answer, answer_limit)
    return PastWorkText(stem=stem, stem_note=stem_note, answer=shown, answer_note=answer_note)


def statement_text(past: PastWork, rule: TextRule, kind: str, record_id: Any, text: Any, limit: int, *,
                   answers: Iterable[Any] = (), items: Iterable[Any] = (),
                   los: Iterable[Any] = ()) -> tuple[str | None, str | None, str | None]:
    """A statement written from ``answers`` and ``items``: ``(text, note,
    withheld)``. Protected inputs withhold it (``withheld`` names why, the
    leakage rule); otherwise the reader's text rule decides."""

    answers, items, los = tuple(answers), tuple(items), tuple(los)
    reason = past.evidence_reason(answers, items)
    if reason:
        return None, None, reason
    shown, note = rule.statement(kind, record_id, text, limit, answers=answers, items=items, los=los)
    return shown, note, None


__all__ = [
    "ANSWER_UNRECORDED",
    "COLD_TASK_KINDS",
    "EXAM_ATTEMPT_TYPES",
    "PINS_UNREADABLE",
    "PROBE_MODES",
    "PROTECTION_UNKNOWN",
    "SNAPSHOT_UNSETTLED",
    "STEM_UNRECORDED",
    "WITHHELD_COLD",
    "WITHHELD_EXAM",
    "WITHHELD_PROBE",
    "WITHHELD_RESERVED",
    "WITHHELD_UNKNOWN_ITEM",
    "WITHHELD_UNREADABLE",
    "PastWork",
    "PastWorkText",
    "PinnedContract",
    "TextRule",
    "Withheld",
    "attempt_protection",
    "attempt_result",
    "frozen_method",
    "held_attempts",
    "hypothesis_answers",
    "past_work_text",
    "pinned_contracts",
    "protection_issues",
    "statement_text",
    "withheld_items",
]
