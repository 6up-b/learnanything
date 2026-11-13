"""What other test files use from ``tests/test_followups_nov2_help_fold.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.version_floor import is_below_floor

from tests.helpers import allow_below_floor
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer, store_map
from tests.hint_fakes import hint_vault as _hint_vault
from tests.hint_h2a_review_round2_helpers import ARGMAX, SELF_GRADE, _call, _context


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
    if is_below_floor(target):
        allow_below_floor(paths.root)
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
