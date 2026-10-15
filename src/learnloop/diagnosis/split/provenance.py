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
owning hypotheses, unresolved-cause factors). :func:`diagnosis_record` turns
it into the closed :class:`~learnloop.db.stores.write_provenance.WriteRecord`
on the writer's connection.

**The snapshot workspace.** The diagnoser opens files of a whole-vault
export itself; the transport reports what it opened
(``workspace_activity``). Each report is mapped to the export entries it
served (:func:`snapshot_reads`): a file read by path or by a plain read
command (``cat``, ``head``, ``tail``, ``sed -n``, ``nl``, ``less``,
``more``, ``wc``) serves that file; a listing (``ls``) or ``cd`` serves
names only. Anything else (a search, a glob, a pipe, a script, a path
outside the export) is counted as reading the WHOLE export. No report at
all leaves the record incomplete.
"""

from __future__ import annotations

import shlex
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

#: A derived text read: ``(kind, record id, its text as shown or None)``.
RecordRead = tuple[str, str, str | None]

#: Why a snapshot diagnosis's record is incomplete when nothing reported its reads.
SNAPSHOT_UNREPORTED = "the snapshot workspace did not report what the diagnoser opened"

_READ_COMMANDS = frozenset({"cat", "head", "tail", "nl", "less", "more", "wc", "sed"})
_NAME_COMMANDS = frozenset({"ls", "cd", "pwd", "echo", "true"})
_SHELLS = frozenset({"bash", "sh", "zsh", "dash"})
_SHELL_OPERATORS = ("|", "&&", "||", ";", ">", "<", "`", "$(", "\n")
_GLOB = frozenset("*?[]{}~")


@dataclass(frozen=True)
class AttemptRead:
    """One attempt shown to the diagnoser. ``grader_text``: a grader's
    output about it was shown too (so its grading is folded in, and its
    item's rubric and reference solution count as read)."""

    attempt_id: str
    grader_text: bool = True


@dataclass(frozen=True)
class DiagnosisReads:
    """What a diagnosis context showed (see the module doc). Pure data."""

    attempts: tuple[AttemptRead, ...] = ()
    solution_items: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    records: tuple[RecordRead, ...] = ()
    factor_attempts: tuple[str, ...] = ()
    unaccounted: tuple[str, ...] = ()

    def join(self, *others: DiagnosisReads) -> DiagnosisReads:
        attempts: dict[str, bool] = {}
        records: dict[tuple[str, str], str | None] = {}
        solution, topics, factors, unaccounted = [], [], [], []
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
        return DiagnosisReads(
            attempts=tuple(AttemptRead(key, value) for key, value in attempts.items()),
            solution_items=tuple(solution),
            topics=tuple(topics),
            records=tuple((kind, record_id, text) for (kind, record_id), text in records.items()),
            factor_attempts=tuple(factors),
            unaccounted=tuple(unaccounted),
        )


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


def attempt_read(attempt: Any) -> DiagnosisReads:
    """A history attempt (``history.HistoryAttempt``) shown."""

    topics = tuple(value for value in (getattr(attempt, "learning_object_id", None),) if value)
    return DiagnosisReads(attempts=(AttemptRead(str(attempt.attempt_id), _grader_text(attempt)),), topics=topics)


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
) -> DiagnosisReads:
    """What an assembled context showed: the diagnosed attempt with its blind
    (or joint) grade, its item's question, rubric and reference solution,
    the neighbourhood's topics, every history attempt rendered, and every
    prior hypothesis, registry statement and repair."""

    reads = DiagnosisReads(
        attempts=(AttemptRead(str(current_attempt_id), True),),
        solution_items=(str(current_item_id),) if current_item_id else (),
        topics=tuple(dict.fromkeys(str(value) for value in (current_learning_object_id, *learning_object_ids)
                                   if value)),
    )
    parts = [attempt_read(attempt) for attempt in attempts]
    parts += [hypothesis_read(record) for record in hypotheses]
    parts += [registry_read(record) for record in registry]
    parts += [repair_read(record) for record in repairs]
    return reads.join(*parts)


# -- the snapshot workspace ------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotEntries:
    """What each exported file serves (``relative path -> DiagnosisReads``)."""

    root: Path
    entries: Mapping[str, DiagnosisReads] = field(default_factory=dict)

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


def _command_files(entries: SnapshotEntries, command: str, depth: int = 0) -> set[str] | str:
    """The export files a reported command read; :data:`_WHOLE` when it
    cannot be accounted for (the whole export counts as read), or
    :data:`_OUTSIDE` when it names a path outside the export."""

    try:
        tokens = shlex.split(command)
    except ValueError:
        return _OUTSIDE if _outside(entries, command.split()) else _WHOLE
    if _outside(entries, tokens):
        return _OUTSIDE
    if depth > 2 or any(operator in command for operator in _SHELL_OPERATORS):
        return _WHOLE
    if not tokens:
        return set()
    program = PurePosixPath(tokens[0]).name
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
            continue
        if token.startswith("-"):
            if program in ("head", "tail") and token in ("-n", "-c"):
                skip_next = True
            elif program == "sed" and token not in ("-n", "--quiet", "--silent"):
                return _WHOLE
            continue
        if program in ("head", "tail") and token.lstrip("+").isdigit():
            continue
        named = _names(entries, token)
        if named is not None and named[0] == "file":
            files |= named[1]
            continue
        if script_pending:
            script_pending = False
            continue
        return _WHOLE
    return files


def snapshot_reads(entries: SnapshotEntries, opened: Sequence[str] | None) -> DiagnosisReads:
    """The export entries the diagnoser's reported activity served (see the
    module doc). ``opened`` None (the transport reported nothing), or a
    report naming a path outside the export, makes the record incomplete; a
    report that cannot be accounted for counts as reading the whole export."""

    if opened is None:
        return DiagnosisReads(unaccounted=(SNAPSHOT_UNREPORTED,))
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
            return entries.whole().join(DiagnosisReads(unaccounted=(SNAPSHOT_OUTSIDE,)))
        if found == _WHOLE:
            whole = True
            continue
        files |= set(found)
    if whole:
        return entries.whole()
    return DiagnosisReads().join(*(entries.entries[path] for path in sorted(files)))


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
    return fold_topic_records(connection, record)


__all__ = [
    "SNAPSHOT_OUTSIDE",
    "SNAPSHOT_UNREPORTED",
    "AttemptRead",
    "DiagnosisReads",
    "RecordRead",
    "SnapshotEntries",
    "attempt_read",
    "diagnosis_record",
    "hypothesis_read",
    "reads_of_context",
    "registry_read",
    "repair_read",
    "snapshot_reads",
]
