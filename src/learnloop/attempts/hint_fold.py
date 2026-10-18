"""Adaptive hints H2a: the submit's fold of shown server hints, taken again at commit (spec §5, G-H2, G-H3).

The submit paths (``submit_attempt``, ``submit_dont_know``) fold the hint
service's shown ``help_assists`` rows into the attempt before grading: levels
1-3 add one each to ``hints_used``, a level 4-5 row sets ``primed``. A second
sidecar on the same vault can deliver a hint of the same submission after that
read and before the attempt commits (review round 2, V1). The invariant: what
an attempt commits equals the fold over this submission's rows shown at the
moment it commits, and no row becomes shown for a submission after its attempt
committed.

:class:`ServerHintFold` records how the submit derived ``hints_used``,
``primed`` and (for an empty stuck answer) the attempt type from the fold, so
:func:`refolded_draft` can take the count again inside the attempt's own
``BEGIN IMMEDIATE`` transaction (``apply_attempt``) and apply the same rule.
Holding the write lock, nothing can be marked shown before the commit, and
``help_assists.mark_shown`` refuses every row once the attempt exists, so the
count read there is final. The values derived from ``hints_used`` and
``primed`` later in the transaction (auto-prime, the eligibility decision, the
activity classification, dampening, the FSRS cap) are computed from the
refolded draft; the grade is reused (no grader sees hints).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop.attempts.stuck import stuck_attempt_type
from learnloop.db.stores.help_assists import attach_keyless_fold, keyless_window_start, server_fold


#: One open workbench problem's help: ``(carried, server)``. ``carried`` is
#: what the problem holds that the client may also send (RW2a: the book once
#: counted and the answer-box hints carried into steps); ``server`` is the
#: problem's own shown checks and level 1-3 hints, which no client count holds.
HeldPart = tuple[int, int]


def combine_held(client_hints: int, parts: tuple[HeldPart, ...] | list[HeldPart]) -> int:
    """The client's count joined with the open problems' help, each distinct
    assist once (RW2b fix round 4, item 4). Only the overlap is deduplicated:
    a carried count the client may hold too (the RW2a book, the carried
    hints) is taken as the larger of the two; the problem's server assists
    (checks, level 1-3 hints) add to it. Over several open problems, the
    larger total (one problem is what the learner worked)."""

    client = int(client_hints)
    return max([client] + [max(client, int(carried)) + int(server) for carried, server in parts])


@dataclass(frozen=True)
class ServerHintFold:
    """One submit's fold of its shown server hints, and the rule it applied."""

    practice_item_id: str
    session_id: str
    submission_id: str | None
    #: A client with no submission key folds the session's rows requested
    #: after this: the item's last attempt in this session (read again at
    #: commit; ``help_assists.mark_shown`` closes the same window, round 3 W1).
    since: str | None
    #: The fold the submit read before grading.
    folded_hints: int
    folded_primed: bool
    #: What the fold is added to: the client's and the tutor questions' hints.
    base_hints: int
    #: The client's priming (and a trace changed after a self-grade disclosure).
    base_primed: bool
    #: The item's ``hint_policy.max_useful_hints`` (0: no clamp).
    max_useful_hints: int = 0
    #: ``submit_attempt`` clamps the total always; ``submit_dont_know`` only
    #: when the fold adds a hint (its behaviour before H2a is unchanged).
    clamp_without_fold: bool = True
    #: An empty stuck answer's attempt type follows ``hints_used``
    #: (``stuck_attempt_type``): the item's allowed types and the probe flag.
    stuck_types: tuple[str, ...] | None = None
    stuck_probe: bool = False
    #: A workbench submit (H2b fix round 3, ruling R1). Its attempt keeps its
    #: own submission key (idempotency, receipts), but its fold is built with
    #: ``submission_id=None``: the window above, the rule H2a already uses
    #: and verified for a keyless submit. So the answer box's hints carry
    #: into steps whatever key they were requested under, the attempt takes
    #: them in its own transaction (:func:`attach_keyless`), and an
    #: answer-box attempt that committed first starts the next window, so
    #: nothing is counted twice (F10). Only the submit-time stamp reads it.
    window_fold: bool = False
    #: When the submission reached the sidecar (H0's admission stamp; None
    #: without a key or telemetry). Fix round 4, F12: the rows the attempt's
    #: transactional refold takes are stamped with it where unstamped (a hint
    #: delivered during grading missed the submit-time stamp). No latency.
    submitted_at: str | None = None
    #: Reader workbench RW2b (fix round 1, F1): the help the item's open
    #: workbench problems hold (Reader §5.4's held rule: their book, carried
    #: hints, shown checks and hints; a workbench submit's own problem is one
    #: of them, still open until its attempt commits), read again inside the
    #: attempt's transaction by ``held_reader`` (the sidecar's callable: the
    #: attempt path never reads the workbench) so a check or hint shown during
    #: grading is counted. With it, ``base_hints`` is
    #: ``combine_held(held_client_hints, held_parts) + held_extra_hints``, as
    #: ``_held_assistance`` computes it before grading (fix round 4, item 4:
    #: the client's count and the problems' server assists add; only the
    #: carried overlap counts once). None: as before RW2b.
    held_reader: Callable[[Any], tuple[tuple[HeldPart, ...], bool]] | None = field(
        default=None, compare=False, repr=False)
    held_client_hints: int = 0
    held_extra_hints: int = 0
    #: The largest help one open problem holds (carried + server): whether
    #: held help makes an independent attempt the assisted type.
    held_hints: int = 0
    held_primed: bool = False
    #: Each open problem's ``(carried, server)`` help (:func:`combine_held`).
    held_parts: tuple[HeldPart, ...] = ()
    #: The item's allowed attempt types: held help makes an independent
    #: attempt the assisted type the answer box picks (``_held_assistance``);
    #: None leaves the type alone (``submit_dont_know``).
    held_types: tuple[str, ...] | None = None

    def base(self) -> int:
        if self.held_reader is None:
            return int(self.base_hints)
        parts = self.held_parts or (((int(self.held_hints), 0),) if self.held_hints else ())
        return combine_held(self.held_client_hints, parts) + int(self.held_extra_hints)

    def hints_used(self, folded: int | None = None) -> int:
        count = self.folded_hints if folded is None else int(folded)
        total = self.base() + count
        if self.max_useful_hints > 0 and (self.clamp_without_fold or count):
            total = min(total, self.max_useful_hints)
        return total

    def primed(self, folded_primed: bool | None = None) -> bool:
        return bool(self.base_primed) or bool(self.held_primed) or bool(
            self.folded_primed if folded_primed is None else folded_primed)

    def attempt_type(self, current: str, folded: int | None = None) -> str:
        if self.stuck_types is None:
            if self.held_types is not None and self.held_hints > 0 and current == "independent_attempt":
                return stuck_attempt_type(list(self.held_types), hints_used=self.held_hints)
            return current
        return stuck_attempt_type(list(self.stuck_types), hints_used=self.hints_used(folded), probe=self.stuck_probe)


def read_fold(connection: Any, *, practice_item_id: str, session_id: str,
              submission_id: str | None) -> tuple[int, bool, str | None]:
    """The fold over the rows shown now, and a keyless submit's window start
    (a vault without ``help_assists`` folds nothing). A keyless submit's
    window is the session's rows requested after the item's last attempt in
    this session: exactly the rows ``mark_shown`` stops showing once this
    attempt commits (round 3, W1)."""

    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
    ).fetchone()
    if exists is None:
        return 0, False, None
    since = None
    if submission_id is None:
        since = keyless_window_start(connection, practice_item_id=practice_item_id, session_id=session_id)
    count, primed = server_fold(connection, practice_item_id=practice_item_id, session_id=session_id,
                                submission_id=submission_id, since=since)
    return count, primed, since


def refolded_draft(connection: Any, draft: Any) -> tuple[Any, ServerHintFold | None]:
    """``draft`` as its submit would have built it from the fold read on
    ``connection`` (the attempt's write transaction), and the new fold when it
    differs from the one read before grading; ``(draft, None)`` when nothing
    changed or the draft carries no fold. Priming is only ever raised: a draft
    the reveal ledger primed stays primed."""

    fold: ServerHintFold | None = getattr(draft, "server_hint_fold", None)
    if fold is None:
        return draft, None
    count, primed, since = read_fold(connection, practice_item_id=fold.practice_item_id,
                                     session_id=fold.session_id, submission_id=fold.submission_id)
    held = (fold.held_hints, fold.held_primed, tuple(fold.held_parts))
    if fold.held_reader is not None:
        # RW2b (fix round 1, F1): the open problems' help, under the same
        # lock; only ever raised (a problem another process submitted in
        # between keeps the count read before grading). Fix round 4, item 4:
        # the same rule as before grading (:func:`combine_held`).
        now_parts, now_primed = fold.held_reader(connection)
        now_parts = tuple((int(carried), int(server)) for carried, server in now_parts)
        before = combine_held(fold.held_client_hints, fold.held_parts)
        parts = now_parts if combine_held(fold.held_client_hints, now_parts) >= before else tuple(fold.held_parts)
        largest = max((carried + server for carried, server in parts), default=0)
        held = (max(largest, int(fold.held_hints)), bool(now_primed) or bool(fold.held_primed), parts)
    if since != fold.since:
        # The window the attempt attaches (:func:`attach_keyless`) is the one
        # read here, under the write lock.
        draft = replace(draft, server_hint_fold=replace(fold, since=since))
        fold = draft.server_hint_fold
    if (count, primed) == (fold.folded_hints, fold.folded_primed) and held == (
            fold.held_hints, fold.held_primed, tuple(fold.held_parts)):
        return draft, None
    now = replace(fold, folded_hints=count, folded_primed=primed, since=since, held_hints=held[0],
                  held_primed=held[1], held_parts=held[2])
    return replace(
        draft,
        hints_used=now.hints_used(),
        primed=now.primed() or bool(draft.primed and not fold.primed()),
        attempt_type=now.attempt_type(draft.attempt_type),
        server_hint_fold=now,
    ), now


def attach_keyless(connection: Any, draft: Any, attempt_id: str) -> int:
    """A keyless submit's attempt takes the rows its fold counted (round 3b),
    in its own write transaction after the attempt row exists: the window
    :func:`refolded_draft` read under the same lock. A keyed submit's rows are
    attached by H0's attach, by key, as before. Returns how many it attached."""

    fold: ServerHintFold | None = getattr(draft, "server_hint_fold", None)
    if fold is None or fold.submission_id is not None:
        return 0
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
    ).fetchone()
    if exists is None:
        return 0
    return attach_keyless_fold(connection, practice_item_id=fold.practice_item_id, session_id=fold.session_id,
                               since=fold.since, attempt_id=attempt_id, submitted_at=fold.submitted_at)


__all__ = ["HeldPart", "ServerHintFold", "attach_keyless", "combine_held", "read_fold", "refolded_draft"]
