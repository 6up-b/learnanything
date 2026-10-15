"""What a diagnosis read, recorded with it (spec_mcp_frontend_c1 §4.8).

Owner decision 2026-10-14 ("land narrow, then fix source"): a diagnosis
records exactly what its context showed the diagnoser, in the transaction
that writes it, so the chat frontend can release its summary (and what is
written from it) once every input is safe. Inputs are recorded at the
source, never inferred from the output.

:class:`DiagnosisReads` is the pure half, computed from the assembled
context (:func:`reads_of_context`) and, in the ``snapshot`` mode, from the
read-only workspace's activity (:func:`snapshot_reads`): every attempt shown
(and whether a grader's output about it was shown: its failed criteria,
fatal errors or first-divergence quotes, written by a grader that read the
item's rubric and reference solution), the items whose rubric and reference
solution were shown directly (the diagnosed attempt's), the topics named,
and the derived texts read (prior hypotheses, registry statements, repairs'
owning hypotheses, unresolved-cause factors), and the name each topic was
shown by (``titles``). :func:`diagnosis_record` turns it into the closed
:class:`~learnloop.db.stores.write_provenance.WriteRecord` on the writer's
connection.

**Frozen when the context is built** (codex review F3). The record is
closed when the context (and, in the ``snapshot`` mode, the export) is
built, before the diagnoser runs (:func:`frozen_record`,
:func:`freeze_entries`), and the diagnosis persists exactly that record: a
regrade while the diagnoser runs never replaces the provenance of what it
was shown. A grading replaced between the history store's read and the
freeze is caught by its identity (``write_provenance.grading_marks``: its
latest blind record, current evidence rows with their contracts, error
events, recorded gradings and C4 receipts). The store reads that identity
in one snapshot with the payloads it shows (codex re-review F3:
``live.live_history_store`` reads it with the blind overlay, and the job
takes the diagnosed attempt's own grade from that overlay); the freeze reads
the record and the identity it is checked against in one snapshot too.

**Topic names** (codex review F2). A generated topic's record covers the
name it was drafted with; it is folded in only when it covers every name
the context showed for the topic (the neighbourhood block's titles, an
exported attempt's topic title, the export's graph file).

**The snapshot workspace.** The diagnoser opens files of a whole-vault
export itself; the transport reports what it opened
(``workspace_activity``). Each report is mapped to the export entries it
served (:func:`snapshot_reads`): a file read by path or by one strictly
validated simple command (:func:`simple_command`: no shell syntax outside
single quotes, so no ``&``, ``;``, ``|``, redirection, substitution,
expansion, escape or line break) of a plain reader (``cat``, ``head``,
``tail``, ``sed -n`` with one print command, ``nl``, ``less``, ``more``,
``wc``) with only output-shaping options serves that file; a listing
(``ls``) or ``cd`` serves names only (export file names are opaque ids).
Anything else (a search, a glob, any shell control syntax, a program that
runs another, a script, a tool item the transport could not read) is
counted as reading the WHOLE export. No report at all, or a path outside
the export, leaves the record incomplete.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

#: A derived text read: ``(kind, record id, its text as shown or None)``.
RecordRead = tuple[str, str, str | None]

#: Why a snapshot diagnosis's record is incomplete when nothing reported its reads.
SNAPSHOT_UNREPORTED = "the snapshot workspace did not report what the diagnoser opened"
#: Why a record is incomplete when a grading it showed was replaced before
#: the record was frozen (codex review F3).
GRADING_REPLACED = "a grading the diagnoser was shown was replaced before its record was frozen"
#: Why a record is incomplete when a grading was shown from a payload the
#: store's caller supplied, which no database row identifies (codex re-review F3).
GRADING_UNIDENTIFIED = "a grading the diagnoser was shown was supplied with no identity to check it against"
#: Why a diagnosis's record is incomplete when nothing froze it when its context was built.
NOT_FROZEN = "what the diagnosis context showed was not frozen when it was built"

_READ_COMMANDS = frozenset({"cat", "head", "tail", "nl", "less", "more", "wc", "sed"})
_NAME_COMMANDS = frozenset({"ls", "cd", "pwd", "echo", "true"})
_SHELLS = frozenset({"bash", "sh", "zsh", "dash"})
#: Shell syntax that is never part of one simple command when it stands
#: outside quotes: control operators (``&`` alone included), redirections,
#: subshells, substitutions, expansions and escapes (codex review F1).
_UNQUOTED_SYNTAX = frozenset("&|;<>()`$\\")
#: ... and inside double quotes: substitution, expansion, escapes.
_DOUBLE_QUOTED_SYNTAX = frozenset("`$\\")
_GLOB = frozenset("*?[]{}~")
#: The only ``sed`` script accounted for: print a line or a line range.
_SED_PRINT = re.compile(r"(\d+|\$)(,(\d+|\$|\+\d+))?p")
#: The options of each read command that only shape its output (any other
#: option, such as ``wc --files0-from`` or ``less -o``, may read or write
#: another file, so the command counts as reading the whole export).
_READ_OPTIONS: dict[str, re.Pattern[str]] = {
    "cat": re.compile(r"-[AbeEnstTuv]+|--(number|number-nonblank|show-all|show-ends|show-nonprinting|"
                      r"show-tabs|squeeze-blank)"),
    "head": re.compile(r"-[nc]|-[nc]?\d+|-[qvz]+|--(lines|bytes)=\d+|--(quiet|silent|verbose|zero-terminated)"),
    "tail": re.compile(r"-[nc]|-[nc]?\+?\d+|-[qvz]+|--(lines|bytes)=\+?\d+|--(quiet|silent|verbose|zero-terminated)"),
    "nl": re.compile(r"-b[atn]|-n(ln|rn|rz)|-w\d+|-v\d+|-i\d+"),
    "wc": re.compile(r"-[clmwL]+|--(bytes|chars|lines|words|max-line-length)"),
    "sed": re.compile(r"-n|--quiet|--silent"),
    "less": re.compile(r"(?!)"),
    "more": re.compile(r"(?!)"),
}


@dataclass(frozen=True)
class AttemptRead:
    """One attempt shown to the diagnoser. ``grader_text``: a grader's
    output about it was shown too (so its grading is folded in, and its
    item's rubric and reference solution count as read)."""

    attempt_id: str
    grader_text: bool = True


@dataclass(frozen=True)
class DiagnosisReads:
    """What a diagnosis context showed (see the module doc). Pure data.
    ``titles``: each ``(topic, name)`` the context showed a topic's name
    as (codex review F2), so a generated topic's record is folded only when
    it covers that name."""

    attempts: tuple[AttemptRead, ...] = ()
    solution_items: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    records: tuple[RecordRead, ...] = ()
    factor_attempts: tuple[str, ...] = ()
    unaccounted: tuple[str, ...] = ()
    titles: tuple[tuple[str, str], ...] = ()

    def join(self, *others: DiagnosisReads) -> DiagnosisReads:
        attempts: dict[str, bool] = {}
        records: dict[tuple[str, str], str | None] = {}
        solution, topics, factors, unaccounted, titles = [], [], [], [], []
        for reads in (self, *others):
            for read in reads.attempts:
                attempts[read.attempt_id] = attempts.get(read.attempt_id, False) or read.grader_text
            for kind, record_id, text in reads.records:
                key = (kind, record_id)
                records[key] = records.get(key) if records.get(key) is not None else text
            solution += [value for value in reads.solution_items if value not in solution]
            topics += [value for value in reads.topics if value not in topics]
            factors += [value for value in reads.factor_attempts if value not in factors]
            unaccounted += [value for value in reads.unaccounted if value not in unaccounted]
            titles += [value for value in reads.titles if value not in titles]
        return DiagnosisReads(
            attempts=tuple(AttemptRead(key, value) for key, value in attempts.items()),
            solution_items=tuple(solution),
            topics=tuple(topics),
            records=tuple((kind, record_id, text) for (kind, record_id), text in records.items()),
            factor_attempts=tuple(factors),
            unaccounted=tuple(unaccounted),
            titles=tuple(titles),
        )

    def title_map(self) -> dict[str, tuple[str, ...]]:
        """``{topic: every name it was shown as}``."""

        found: dict[str, list[str]] = {}
        for topic, title in self.titles:
            found.setdefault(topic, []).append(title)
        return {topic: tuple(values) for topic, values in found.items()}


def shown_titles(vault: Any, topics: Iterable[Any]) -> tuple[tuple[str, str], ...]:
    """``(topic, its title)`` for each topic a context rendered by name, as
    the vault it rendered from holds it (codex review F2)."""

    los = getattr(vault, "learning_objects", None) or {}
    found: list[tuple[str, str]] = []
    for topic in topics:
        lo = los.get(str(topic or ""))
        title = getattr(lo, "title", None) if lo is not None else None
        if title is not None and (str(topic), str(title)) not in found:
            found.append((str(topic), str(title)))
    return tuple(found)


def _grader_text(attempt: Any) -> bool:
    return bool(getattr(attempt, "failed_criteria", ()) or getattr(attempt, "fatal_errors", ())
                or getattr(attempt, "first_divergence_quotes", ()))


def hypothesis_read(record: Any) -> DiagnosisReads:
    """A prior hypothesis record (``history.HypothesisRecord``) read."""

    kind = str(getattr(record, "kind", "") or "")
    topics = tuple(value for value in (getattr(record, "learning_object_id", None),) if value)
    if kind == "unresolved_factor":
        source = getattr(record, "source_attempt_id", None)
        return DiagnosisReads(topics=topics, factor_attempts=(str(source),) if source else (),
                              unaccounted=() if source else ("an unresolved-cause factor with no attempt",))
    target = {"causal_hypothesis": "hypothesis", "misconception": "misconception"}.get(kind)
    if target is None:
        return DiagnosisReads(topics=topics, unaccounted=(f"a prior record of an unknown kind ({kind})",))
    return DiagnosisReads(topics=topics, records=((target, str(record.id), str(record.statement or "")),))


def registry_read(record: Any) -> DiagnosisReads:
    """A registry record (``history.RegistryRecord``) read."""

    kind = {"durable": "misconception", "candidate": "candidate"}.get(str(getattr(record, "kind", "") or ""))
    topics = tuple(value for value in (getattr(record, "learning_object_id", None),) if value)
    if kind is None:
        return DiagnosisReads(topics=topics, unaccounted=(f"a registry record of an unknown kind ({record.kind})",))
    return DiagnosisReads(topics=topics, records=((kind, str(record.id), str(record.statement or "")),))


def repair_read(record: Any) -> DiagnosisReads:
    """A repair record (``history.RepairRecord``): its operator was written
    with its owning hypotheses, whose records are folded in."""

    return DiagnosisReads(records=tuple(("hypothesis", str(value), None)
                                        for value in getattr(record, "hypothesis_ids", ()) or () if value))


def attempt_read(attempt: Any, *, title: str | None = None) -> DiagnosisReads:
    """A history attempt (``history.HistoryAttempt``) shown, with its
    topic's name when the rendering showed one (``title``)."""

    topics = tuple(value for value in (getattr(attempt, "learning_object_id", None),) if value)
    titles = ((str(topics[0]), str(title)),) if topics and title is not None else ()
    return DiagnosisReads(attempts=(AttemptRead(str(attempt.attempt_id), _grader_text(attempt)),), topics=topics,
                          titles=titles)


def reads_of_context(
    *,
    current_attempt_id: str,
    current_item_id: str,
    current_learning_object_id: str,
    learning_object_ids: Iterable[str],
    attempts: Iterable[Any],
    hypotheses: Iterable[Any],
    registry: Iterable[Any],
    repairs: Iterable[Any],
    titles: Iterable[tuple[str, str]] = (),
) -> DiagnosisReads:
    """What an assembled context showed: the diagnosed attempt with its blind
    (or joint) grade, its item's question, rubric and reference solution,
    the neighbourhood's topics (``titles``: the names it showed them by),
    every history attempt rendered, and every prior hypothesis, registry
    statement and repair."""

    reads = DiagnosisReads(
        attempts=(AttemptRead(str(current_attempt_id), True),),
        solution_items=(str(current_item_id),) if current_item_id else (),
        topics=tuple(dict.fromkeys(str(value) for value in (current_learning_object_id, *learning_object_ids)
                                   if value)),
        titles=tuple(titles),
    )
    parts = [attempt_read(attempt) for attempt in attempts]
    parts += [hypothesis_read(record) for record in hypotheses]
    parts += [registry_read(record) for record in registry]
    parts += [repair_read(record) for record in repairs]
    return reads.join(*parts)


# -- the snapshot workspace ------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotEntries:
    """What each exported file serves (``relative path -> DiagnosisReads``),
    and each file's closed record frozen when the export was written
    (``records``, codex review F3: :func:`freeze_entries`)."""

    root: Path
    entries: Mapping[str, DiagnosisReads] = field(default_factory=dict)
    records: Mapping[str, Any] = field(default_factory=dict)

    def whole(self) -> DiagnosisReads:
        return DiagnosisReads().join(*self.entries.values())


def _relative(root: Path, token: str) -> str | None:
    """``token`` as an export path relative to ``root``, or None when it lies outside."""

    path = PurePosixPath(token)
    if path.is_absolute():
        try:
            path = PurePosixPath(Path(token).resolve().relative_to(root.resolve()).as_posix())
        except (ValueError, OSError):
            return None
    parts = [part for part in path.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        return None
    return "/".join(parts)


def _names(entries: SnapshotEntries, token: str) -> tuple[str, set[str]] | None:
    """``("file", {path})`` or ``("dir", {paths under it})`` for an export
    path, or None when the token names nothing in the export."""

    relative = _relative(entries.root, token)
    if relative is None:
        return None
    if relative in entries.entries:
        return "file", {relative}
    prefix = f"{relative}/" if relative else ""
    under = {path for path in entries.entries if path.startswith(prefix)}
    if under or relative == "":
        return "dir", under
    return None


#: What an unaccountable report reads: the whole export, or (it names a path
#: outside the export) something no record can name.
_WHOLE, _OUTSIDE = "whole", "outside"
#: Why a snapshot diagnosis's record is incomplete when it read outside the export.
SNAPSHOT_OUTSIDE = "the diagnoser read a path outside the snapshot export"


def _outside(entries: SnapshotEntries, tokens: Iterable[str]) -> bool:
    for token in tokens:
        for piece in token.replace("=", " ").split():
            if piece.startswith("~") or (piece.startswith("/") and _relative(entries.root, piece) is None):
                return True
            if ".." in PurePosixPath(piece).parts:
                return True
    return False


def simple_command(command: str) -> bool:
    """Whether ``command`` is one simple command (codex review F1): every
    character printable, no line break, quotes closed, and no shell syntax
    outside single quotes (no control operator such as ``&``, ``;`` or
    ``|``, no redirection, subshell, substitution, expansion or escape).
    Anything else can run more than the command the report names."""

    if any(not character.isprintable() for character in command):
        return False
    quote: str | None = None
    for character in command:
        if quote == "'":
            quote = None if character == "'" else quote
        elif quote == '"':
            if character == '"':
                quote = None
            elif character in _DOUBLE_QUOTED_SYNTAX:
                return False
        elif character in ("'", '"'):
            quote = character
        elif character in _UNQUOTED_SYNTAX:
            return False
    return quote is None


def _command_files(entries: SnapshotEntries, command: str, depth: int = 0) -> set[str] | str:
    """The export files a reported command read; :data:`_WHOLE` when it
    cannot be accounted for (the whole export counts as read), or
    :data:`_OUTSIDE` when it names a path outside the export. Only one
    strictly validated simple command (:func:`simple_command`) of a known
    plain read, with only output-shaping options, is accounted for."""

    try:
        tokens = shlex.split(command)
    except ValueError:
        return _OUTSIDE if _outside(entries, command.split()) else _WHOLE
    if _outside(entries, tokens):
        return _OUTSIDE
    if depth > 2 or not simple_command(command):
        return _WHOLE
    if not tokens:
        return set()
    program = PurePosixPath(tokens[0]).name
    if "/" in tokens[0]:
        # A program run from a path inside the workspace: not a plain reader.
        return _WHOLE
    if program in _SHELLS:
        if len(tokens) == 3 and tokens[1] in ("-c", "-lc"):
            return _command_files(entries, tokens[2], depth + 1)
        return _WHOLE
    arguments = tokens[1:]
    if any(_GLOB & set(token) for token in arguments):
        return _WHOLE
    if program in _NAME_COMMANDS:
        # A listing or a change of directory serves names only.
        return set()
    if program not in _READ_COMMANDS:
        return _WHOLE
    files: set[str] = set()
    script_pending = program == "sed"
    skip_next = False
    for token in arguments:
        if skip_next:
            skip_next = False
            if not token.lstrip("+").isdigit():
                return _WHOLE
            continue
        if token == "--":
            continue
        if token.startswith("-") and token != "-":
            if not _READ_OPTIONS[program].fullmatch(token):
                return _WHOLE
            # ``head -n 5``: the count is the next token.
            skip_next = program in ("head", "tail") and token in ("-n", "-c")
            continue
        if program in ("head", "tail") and token.lstrip("+").isdigit():
            continue
        named = _names(entries, token)
        if named is not None and named[0] == "file":
            files |= named[1]
            continue
        if script_pending and _SED_PRINT.fullmatch(token):
            # Only a plain print script (``1,40p``): any other (an ``e``
            # command runs a program, ``w`` writes) counts as the whole export.
            script_pending = False
            continue
        return _WHOLE
    return files


def served_entries(entries: SnapshotEntries, opened: Sequence[str] | None) -> tuple[str, tuple[str, ...]]:
    """What the reported activity served: ``("unreported", ())``,
    ``("outside", every path)``, ``("whole", every path)`` or ``("entries",
    the paths)`` (see the module doc). The diagnosis receipt keeps it."""

    if opened is None:
        return "unreported", ()
    files: set[str] = set()
    whole = False
    for report in opened:
        report = str(report or "").strip()
        if not report:
            continue
        named = None if any(character.isspace() for character in report) else _names(entries, report)
        if named is not None:
            files |= named[1] if named[0] == "file" else set()
            continue
        found = _command_files(entries, report)
        if found == _OUTSIDE:
            return "outside", tuple(sorted(entries.entries))
        if found == _WHOLE:
            whole = True
            continue
        files |= set(found)
    if whole:
        return "whole", tuple(sorted(entries.entries))
    return "entries", tuple(sorted(files))


def snapshot_reads(entries: SnapshotEntries, opened: Sequence[str] | None) -> DiagnosisReads:
    """The export entries the diagnoser's reported activity served
    (:func:`served_entries`). ``opened`` None (the transport reported
    nothing), or a report naming a path outside the export, makes the record
    incomplete; a report that cannot be accounted for counts as reading the
    whole export."""

    how, paths = served_entries(entries, opened)
    if how == "unreported":
        return DiagnosisReads(unaccounted=(SNAPSHOT_UNREPORTED,))
    reads = DiagnosisReads().join(*(entries.entries[path] for path in paths))
    if how == "outside":
        reads = reads.join(DiagnosisReads(unaccounted=(SNAPSHOT_OUTSIDE,)))
    return reads


def snapshot_record(entries: SnapshotEntries, opened: Sequence[str] | None) -> Any:
    """The closed record of what the reported activity served: the records
    of the entries served, as frozen when the export was written (codex
    review F3), plus why it is incomplete (:func:`snapshot_reads`)."""

    from learnloop.db.stores.write_provenance import WriteRecord

    how, paths = served_entries(entries, opened)
    if how == "unreported":
        return WriteRecord.incomplete(SNAPSHOT_UNREPORTED)
    record = WriteRecord()
    for path in paths:
        frozen = entries.records.get(path)
        record = record.join(frozen if isinstance(frozen, WriteRecord)
                             else WriteRecord.incomplete(f"{NOT_FROZEN} ({path})"))
    if how == "outside":
        record = record.join(WriteRecord.incomplete(SNAPSHOT_OUTSIDE))
    return record


# -- the record ------------------------------------------------------------------------


def diagnosis_record(connection: Any, reads: DiagnosisReads) -> Any:
    """The diagnosis's closed write-time record, on the writer's connection:
    every attempt read under its pinned contract (with its grading folded in
    when a grader's output about it was shown), the items whose rubric and
    reference solution were read, the topics, and the recorded inputs of
    every derived text read. Incomplete when anything read cannot be
    accounted for."""

    from learnloop.db.stores.write_provenance import (
        GRADING,
        Inputs,
        WriteRecord,
        answer_inputs,
        attempt_statement_refs,
        closure,
        fold_topic_records,
    )

    inputs = Inputs.of(items=reads.solution_items, solution_items=reads.solution_items, topics=reads.topics)
    graded = [read.attempt_id for read in reads.attempts if read.grader_text]
    plain = [read.attempt_id for read in reads.attempts if not read.grader_text]
    inputs = inputs.union(answer_inputs(connection, graded, solution=True)).union(answer_inputs(connection, plain))
    refs: list[tuple[str, str]] = [(GRADING, attempt_id) for attempt_id in graded]
    texts: dict[tuple[str, str], Any] = {}
    for kind, record_id, text in reads.records:
        refs.append((kind, record_id))
        if text is not None:
            texts[(kind, record_id)] = text
    for attempt in reads.factor_attempts:
        inputs = inputs.union(answer_inputs(connection, [attempt]))
        refs.extend(attempt_statement_refs(connection, attempt, every_diagnosis=True))
    record = WriteRecord(inputs).join(closure(connection, refs, texts=texts))
    for reason in reads.unaccounted:
        record = record.join(WriteRecord.incomplete(reason))
    return fold_topic_records(connection, record, titles=reads.title_map())


def _read_attempts(reads: DiagnosisReads) -> list[str]:
    return list(dict.fromkeys([*(read.attempt_id for read in reads.attempts), *reads.factor_attempts]))


def _replaced(shown: Mapping[str, str], now: Mapping[str, str], attempts: Iterable[str]) -> Any:
    """Incomplete for every attempt whose grading changed since the history
    read what it showed (``shown``: :meth:`VaultHistoryStore.grading_marks`,
    read in one snapshot with the payloads shown; ``now``:
    ``write_provenance.grading_marks``, read in one snapshot with the record),
    and for every grading shown from a payload no database row identifies
    (codex re-review F3)."""

    from learnloop.db.stores.write_provenance import UNIDENTIFIED_GRADING, WriteRecord, grading_mark

    ungraded = grading_mark()
    read = list(dict.fromkeys(str(value) for value in attempts if value))
    unidentified = sorted(attempt for attempt in read if shown.get(attempt) == UNIDENTIFIED_GRADING)
    changed = sorted(attempt for attempt in read if attempt not in unidentified
                     and shown.get(attempt, ungraded) != now.get(attempt, ungraded))
    record = WriteRecord()
    if unidentified:
        record = record.join(WriteRecord.incomplete(f"{GRADING_UNIDENTIFIED} ({', '.join(unidentified)})"))
    if changed:
        record = record.join(WriteRecord.incomplete(f"{GRADING_REPLACED} ({', '.join(changed)})"))
    return record


def frozen_record(store: Any, reads: DiagnosisReads) -> Any:
    """THE record of what a diagnosis context showed, frozen when the context
    is built (codex review F3): every contract, grading and derived text's
    record as it stands now, before the diagnoser runs, so a regrade while
    it runs never replaces the provenance of what it was shown. Each grading
    shown (a history attempt's, and the diagnosed attempt's own) is checked
    against the identity the store read with its payload (codex re-review
    F3): one replaced since is named, and a store that cannot say what it
    showed makes the record incomplete."""

    from learnloop.db.stores.write_provenance import WriteRecord, grading_marks, read_snapshot

    repository = getattr(store, "repository", None)
    marks = getattr(store, "grading_marks", None)
    if repository is None or not callable(marks):
        return WriteRecord.incomplete(NOT_FROZEN)
    shown = marks()
    attempts = _read_attempts(reads)
    # The record and the identities it is checked against, in one snapshot.
    with repository.connection() as connection, read_snapshot(connection):
        record = diagnosis_record(connection, reads)
        now = grading_marks(connection, attempts)
    return record.join(_replaced(shown, now, attempts))


def freeze_entries(store: Any, entries: Mapping[str, DiagnosisReads]) -> dict[str, Any]:
    """Each export file's closed record, frozen when the export is written
    (codex review F3); :func:`snapshot_record` joins the ones served."""

    from learnloop.db.stores.write_provenance import WriteRecord, grading_marks, read_snapshot

    repository = getattr(store, "repository", None)
    marks = getattr(store, "grading_marks", None)
    if repository is None or not callable(marks):
        return {path: WriteRecord.incomplete(NOT_FROZEN) for path in entries}
    with repository.connection() as connection, read_snapshot(connection):
        frozen = {path: diagnosis_record(connection, reads) for path, reads in entries.items()}
        attempts = {path: _read_attempts(reads) for path, reads in entries.items()}
        now = grading_marks(connection, [attempt for ids in attempts.values() for attempt in ids])
    shown = marks()
    return {path: record.join(_replaced(shown, now, attempts[path])) for path, record in frozen.items()}


__all__ = [
    "GRADING_REPLACED",
    "GRADING_UNIDENTIFIED",
    "NOT_FROZEN",
    "SNAPSHOT_OUTSIDE",
    "SNAPSHOT_UNREPORTED",
    "AttemptRead",
    "DiagnosisReads",
    "RecordRead",
    "SnapshotEntries",
    "attempt_read",
    "diagnosis_record",
    "freeze_entries",
    "frozen_record",
    "hypothesis_read",
    "reads_of_context",
    "registry_read",
    "repair_read",
    "served_entries",
    "shown_titles",
    "simple_command",
    "snapshot_reads",
    "snapshot_record",
]
