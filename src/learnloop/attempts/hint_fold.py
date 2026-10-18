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

from dataclasses import dataclass, replace
from typing import Any

from learnloop.attempts.stuck import stuck_attempt_type
from learnloop.db.stores.help_assists import (
    attach_carried_fold,
    attach_keyless_fold,
    carried_fold,
    keyless_window_start,
    server_fold,
)


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
    #: A workbench submit's problem (H2b review F1): the answer box's shown
    #: server hints carried into it (``help_assists.workbench_session_id``)
    #: fold in too, by the same rule, and attach to its attempt.
    workbench_session_id: str | None = None

    def hints_used(self, folded: int | None = None) -> int:
        count = self.folded_hints if folded is None else int(folded)
        total = int(self.base_hints) + count
        if self.max_useful_hints > 0 and (self.clamp_without_fold or count):
            total = min(total, self.max_useful_hints)
        return total

    def primed(self, folded_primed: bool | None = None) -> bool:
        return bool(self.base_primed) or bool(self.folded_primed if folded_primed is None else folded_primed)

    def attempt_type(self, current: str, folded: int | None = None) -> str:
        if self.stuck_types is None:
            return current
        return stuck_attempt_type(list(self.stuck_types), hints_used=self.hints_used(folded), probe=self.stuck_probe)


def read_fold(connection: Any, *, practice_item_id: str, session_id: str,
              submission_id: str | None, workbench_session_id: str | None = None) -> tuple[int, bool, str | None]:
    """The fold over the rows shown now, and a keyless submit's window start
    (a vault without ``help_assists`` folds nothing). A keyless submit's
    window is the session's rows requested after the item's last attempt in
    this session: exactly the rows ``mark_shown`` stops showing once this
    attempt commits (round 3, W1). A workbench submit adds the answer box's
    rows carried into its problem (H2b review F1)."""

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
    if workbench_session_id is not None:
        carried, carried_primed, _rows = carried_fold(
            connection, practice_item_id=practice_item_id, workbench_session_id=workbench_session_id,
            exclude_submission_id=submission_id)
        count, primed = count + carried, primed or carried_primed
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
                                     session_id=fold.session_id, submission_id=fold.submission_id,
                                     workbench_session_id=fold.workbench_session_id)
    if since != fold.since:
        # The window the attempt attaches (:func:`attach_keyless`) is the one
        # read here, under the write lock.
        draft = replace(draft, server_hint_fold=replace(fold, since=since))
        fold = draft.server_hint_fold
    if (count, primed) == (fold.folded_hints, fold.folded_primed):
        return draft, None
    now = replace(fold, folded_hints=count, folded_primed=primed, since=since)
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
                               since=fold.since, attempt_id=attempt_id)


def attach_carried(connection: Any, draft: Any, attempt_id: str) -> int:
    """A workbench attempt takes the answer box's rows carried into its
    problem that its fold counted (H2b review F1), in its own write
    transaction after the attempt row exists, so no later fold (the answer
    box's key included) counts them again. Returns how many it attached."""

    fold: ServerHintFold | None = getattr(draft, "server_hint_fold", None)
    if fold is None or fold.workbench_session_id is None:
        return 0
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
    ).fetchone()
    if exists is None:
        return 0
    return attach_carried_fold(connection, practice_item_id=fold.practice_item_id,
                               workbench_session_id=fold.workbench_session_id, attempt_id=attempt_id,
                               exclude_submission_id=fold.submission_id)


__all__ = ["ServerHintFold", "attach_carried", "attach_keyless", "read_fold", "refolded_draft"]
