"""Follow-ups Nov 2 (b): the help fold counts exactly the help rows that attach.

Closes the queued follow-up "the help fold counts exactly the help rows that
attach (all help kinds; session rollover case)". Before it, a keyed submit's
fold read only the rows of its key requested in the submit's own practice
session, while H0's attach takes every row of the key, any session: a hint
shown under the key in a session that then ended (the learner went on in a new
session with the same draft) was attached to the attempt without being counted
(``hints_used`` 0, certification eligible, beside an attached shown hint).

Now the keyed fold reads by the key alone (H0's attach rule), and a keyed
attempt takes the rows it counted in its own write transaction, through the
fold's own row definition (``help_assists._fold_rows``), so whichever help
kinds the fold counts are the kinds it attaches, and no other attempt can take
a counted row between the commit and H0's attach.

Replay re-applies the stored ``hints_used`` and never refolds
(``attempts._refold_server_hints``); only new attempts change. It changes which
new attempts are primed, so it is the successor mvp-0.42 (built as mvp-0.41) with the kill switch
``hints.fold_follows_attach`` (Codex review F1; the gate and the upgrade are
pinned in ``tests/test_help_fold_attach_successor.py``): these tests run at the
tag. Fakes only.
"""

from __future__ import annotations

from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.connection import connect
from tests.approach_map_fakes import LO
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, prefer, store_map
from tests.hint_fakes import hint_vault as _hint_vault
from tests.test_hint_h2a_review_round2 import ARGMAX, SELF_GRADE, _attempt, _call, _context


def hint_vault(tmp_path, *, version: str | None = None, **kwargs):
    """The hint vault at the successor's tag (Codex review F1: the fold below is
    mvp-0.42's, behind ``hints.fold_follows_attach``), or at ``version``."""

    from learnloop.algorithm_versions import HELP_FOLD_ATTACH_ALGORITHM_VERSION
    from learnloop.ops.vault_upgrade import rewrite_algorithm_version
    from learnloop.vault.loader import load_vault

    paths = _hint_vault(tmp_path, **kwargs)
    current = load_vault(paths.root).config.algorithms.algorithm_version
    target = version or HELP_FOLD_ATTACH_ALGORITHM_VERSION
    if current != target:
        rewrite_algorithm_version(paths.root / "learnloop.toml", current, target, durable=True)
    return paths

def _hinted_session(paths, ctx, *, key: str = "k1", option: str = "next_step@L3") -> str:
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    params = {"sessionId": session, "practiceItemId": ITEM, "submissionId": key, "answerMd": WORK}
    if option.endswith(("L4", "L5")):
        params["takenLevel"] = int(option[-1])
    job = _call(ctx, "practice.request_hint", params)
    assert job["result"]["shown"] is True
    return session


def _rollover(tmp_path, *, config: str = ARGMAX, option: str = "next_step@L3", version: str | None = None):
    """A hint shown under ``k1`` in session one; session one ends; the same
    draft (same key) is submitted in session two."""

    paths = hint_vault(tmp_path, config=config, version=version)
    store_map(paths)
    ctx = _context(paths, inline=True)
    first = _hinted_session(paths, ctx, option=option)
    _call(ctx, "end_session", {"sessionId": first})
    second = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    assert second != first
    return paths, ctx, first, second


def _submit(ctx, session, *, key: str | None = "k1", hints: int = 0, rpc: str = "submit_attempt"):
    params = {"sessionId": session, "practiceItemId": ITEM}
    if key is not None:
        params["submissionId"] = key
    if rpc == "submit_attempt":
        params.update({"answerMd": WORK, "attemptType": "independent_attempt", "hintsUsed": hints,
                       "selfGrade": SELF_GRADE})
    return _call(ctx, rpc, params)


@pytest.mark.parametrize("rpc", ["submit_attempt", "submit_dont_know"])
def test_session_rollover_a_hint_shown_under_the_key_in_an_ended_session_is_counted_where_it_attaches(
        tmp_path, rpc):
    """The follow-up's session rollover case: before the fix the attempt
    recorded ``hints_used`` 0 while the shown hint was attached to it."""

    paths, ctx, first, second = _rollover(tmp_path)
    result = _submit(ctx, second, rpc=rpc)
    attempt = _attempt(paths, result["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert row["practice_session_id"] == first and row["shown"] == 1
    assert row["attempt_id"] == result["attemptId"]
    assert attempt["hints_used"] == 1


def test_session_rollover_worked_help_primes_the_attempt_it_attaches_to(tmp_path):
    paths, ctx, _first, second = _rollover(tmp_path, option="worked_chunk@L4")
    result = _submit(ctx, second)
    attempt = _attempt(paths, result["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert row["level"] == 4 and row["attempt_id"] == result["attemptId"]
    assert attempt["primed"] == 1 and attempt["hints_used"] == 0


def test_a_counted_row_is_attached_in_the_attempts_own_transaction(tmp_path, monkeypatch):
    """No other attempt can take a counted row between the commit and H0's
    attach: the keyed attempt has it before H0's attach runs at all."""

    from learnloop_sidecar.handlers import practice as practice_handlers

    paths, ctx, _first, second = _rollover(tmp_path)
    monkeypatch.setattr(practice_handlers, "_attach_hint_reveals", lambda *args, **kwargs: None)
    result = _submit(ctx, second)
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == result["attemptId"]
    assert _attempt(paths, result["attemptId"])["hints_used"] == 1
    # A keyless submit back in the first session's window finds nothing left.
    keyless = _submit(ctx, _call(ctx, "start_session", {"energy": "medium"})["sessionId"], key=None)
    assert _attempt(paths, keyless["attemptId"])["hints_used"] == 0


def test_the_same_session_keyed_flow_is_unchanged(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = _context(paths, inline=True)
    session = _hinted_session(paths, ctx)
    result = _submit(ctx, session)
    [row] = assists(paths.sqlite_path)
    assert _attempt(paths, result["attemptId"])["hints_used"] == 1
    assert row["attempt_id"] == result["attemptId"] and row["submitted_at"] is not None


def test_another_keys_rows_are_never_counted_or_taken(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = _context(paths, inline=True)
    session = _hinted_session(paths, ctx, key="k_other")
    result = _submit(ctx, session)
    [row] = assists(paths.sqlite_path)
    assert _attempt(paths, result["attemptId"])["hints_used"] == 0
    assert row["attempt_id"] is None


# ---------------------------------------------------------------------------
# All help kinds: the attach is the fold's own row definition
# ---------------------------------------------------------------------------

def _row(connection, assist_id: str, *, kind: str, session: str, key: str, level: int | None = 2,
         counted_by: str | None = "server", shown: int = 1) -> None:
    from learnloop.db.stores.help_assists import insert_assist

    insert_assist(connection, {
        "id": assist_id, "surface": "practice", "assist_kind": kind, "practice_item_id": ITEM,
        "practice_session_id": session, "submission_id": key, "hint_kind": "next_step" if kind == "hint" else None,
        "level": level, "chooser": "fallback", "shown": shown, "counted_by": counted_by,
        "requested_at": "2026-11-02T09:00:00Z"})


def _attempt_row(connection, attempt_id: str, session: str, key: str) -> None:
    connection.execute(
        "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "learner_answer_md, correctness, created_at, session_id, submission_id) "
        "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', '', 0.0, '2026-11-02T10:00:00Z', ?, ?)",
        (attempt_id, ITEM, LO, session, key))


KINDS = ("hint", "check", "discriminate_answer", "bridge", "example", "compare_methods", "feedback")


def test_every_help_kind_the_keyed_fold_counts_is_exactly_what_the_attempt_attaches(tmp_path):
    """Whatever kinds ``_fold_rows`` counts (hints today; RW5d P3 adds its
    figure rows to the same definition), the keyed attach takes exactly those
    rows, in every session of the key, and nothing it does not count."""

    from learnloop.db.stores.help_assists import attach_keyed_fold, fold_row_count, server_fold

    paths = hint_vault(tmp_path, config=ARGMAX)
    with closing(connect(paths.sqlite_path)) as connection:
        for index, kind in enumerate(KINDS):
            for session in ("s_old", "s_new"):
                _row(connection, f"ha_{kind}_{session}", kind=kind, session=session, key="k1")
                _row(connection, f"ha_{kind}_{session}_client", kind=kind, session=session, key="k1",
                     counted_by="client")
                _row(connection, f"ha_{kind}_{session}_unshown", kind=kind, session=session, key="k1", shown=0)
                _row(connection, f"ha_{kind}_{session}_other", kind=kind, session=session, key="k2")
        _row(connection, "ha_worked", kind="hint", session="s_old", key="k1", level=4)
        connection.commit()
        counted = fold_row_count(connection, practice_item_id=ITEM, session_id="s_new", submission_id="k1",
                                 any_session=True)
        hints, primed = server_fold(connection, practice_item_id=ITEM, session_id="s_new", submission_id="k1",
                                    any_session=True)
        _attempt_row(connection, "att_k1", "s_new", "k1")
        attached = attach_keyed_fold(connection, practice_item_id=ITEM, session_id="s_new", submission_id="k1",
                                     attempt_id="att_k1")
        connection.commit()
        taken = {row[0] for row in connection.execute("SELECT id FROM help_assists WHERE attempt_id = 'att_k1'")}
    assert attached == counted == len(taken)
    assert hints == 2 and primed is True  # the hint in both sessions; the worked one primes
    assert taken == {"ha_hint_s_old", "ha_hint_s_new", "ha_worked"}


def test_the_keyless_window_still_reads_its_own_session_only(tmp_path):
    """The window rule (H2a round 3, W1) is unchanged: a keyless submit folds
    and attaches only its session's rows since the item's last attempt there."""

    from learnloop.attempts.hint_fold import read_fold

    paths = hint_vault(tmp_path, config=ARGMAX)
    with closing(connect(paths.sqlite_path)) as connection:
        _row(connection, "ha_a", kind="hint", session="s_old", key="k1")
        _row(connection, "ha_b", kind="hint", session="s_new", key="k1")
        connection.commit()
        assert read_fold(connection, practice_item_id=ITEM, session_id="s_new", submission_id=None) == (1, False, None)
        assert read_fold(connection, practice_item_id=ITEM, session_id="s_new", submission_id="k1",
                         any_session=True) == (2, False, None)
        # The predecessor's keyed fold (below the tag or switched off): its session only.
        assert read_fold(connection, practice_item_id=ITEM, session_id="s_new", submission_id="k1") == (
            1, False, None)
