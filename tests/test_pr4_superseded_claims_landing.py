"""Landing of mobile PR-3/PR-4 onto main (``docs/reviews/mobile-pr3-pr4.md``, "Landing onto main").

Interaction (i): the kept replaced claims' replace seam (successor mvp-0.36,
``Repository.replace_learner_claim``, atomic with the LO's re-anchor) against
PR-4's attempt write (successor mvp-0.37, ``practice.attempt_keeps_content_state``)
and PR-4's session ownership, in one session on the desktop sidecar:

* the desktop starts a session and answers an item, retires it ``too_easy``
  (the first learner report on its LO), then answers a second item of the
  same LO while a second ``too_easy`` retirement of that item commits between
  the grading and the attempt's transaction (another writer on the same
  vault). The second report replaces the first (kept, ``superseded_by``) and
  re-anchors the LO; the attempt's write keeps the retired row closed and its
  content hash as the retirement left it;
* a retirement is not session-scoped (spec_mobile_tailnet_v1 §9.5 lists the
  session-scoped writes that check ownership: the submit's acceptance is one,
  ``retire_practice_item`` is not), so after a phone adopts the session the
  desktop's submit is ``session_moved`` and writes nothing, while its
  retirement of another item still lands, with its own claim and re-anchor;
* a shadow rebuild agrees with live: 0/0/0.

Interaction (iii): main's AD denial-log archival at upgrade (416a9ddfe)
archives the log once per `upgrade --to mvp-0.37` command, chained from
mvp-0.35 too, and a refused upgrade leaves it in place. Interaction (ii) is in
``tests/test_attempt_content_state_successor.py``.

Fakes only: self-graded attempts, no model call.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest

import learnloop.attempts.attempts as attempts_module
import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.repositories import Repository
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import NOW
from tests.test_learner_report_superseded import _vault
from tests.test_rebuild_equivalence import ZERO, _shadow_summary

PHONE = "dev_phone"


#: The sidecar's writes read the system clock. A real clock leaves
#: sub-second live times where the ledger stores whole seconds (~1e-9 logit
#: and 1 s due-time noise between live and a rebuild at any version, the
#: predecessor's included), so the system clock is held at whole seconds and
#: each step advances it explicitly, from after the fixture vault's sync.
_CLOCK = {"now": NOW}


@pytest.fixture(autouse=True)
def _stepped_clock(monkeypatch):
    _CLOCK["now"] = NOW + timedelta(hours=1)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: _CLOCK["now"])


def _step(minutes: int = 3) -> None:
    _CLOCK["now"] = _CLOCK["now"] + timedelta(minutes=minutes)


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _submit(ctx: SidecarContext, session_id: str, item_id: str, points: float) -> dict:
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": "An answer.",
        "attemptType": "independent_attempt",
        "selfGrade": {"criterionPoints": {"correctness": points}, "confidence": 4},
    })


def _claims(repository: Repository) -> list[dict]:
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT id, scope_id, superseded_by FROM learner_claims WHERE source = 'learner_report' "
            "ORDER BY created_at, id")]


def _attempts(repository: Repository) -> int:
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0])


def _retire_before_the_attempt_commits(monkeypatch, paths, item_id: str) -> dict:
    """Another writer retires ``item_id`` too_easy after the answer was graded
    and before the attempt's transaction opens (PR-2's reverse race, here
    with mvp-0.36's replace seam inside the retirement)."""

    original = attempts_module.apply_attempt
    seen: dict = {}

    def retire_then_apply(vault, repository, attempt, *, clock=None):
        if "retired" not in seen and not attempt.replace_existing and attempt.draft.practice_item_id == item_id:
            other = Repository(paths.sqlite_path)
            # Between the grading and the attempt's transaction: a minute later on the system clock.
            _step(1)
            retire_item(paths.root, other, practice_item_id=item_id, reason="too_easy")
            _step(1)
            seen["retired"] = Repository.attach(paths.sqlite_path).practice_item_state(item_id)
        return original(vault, repository, attempt, clock=clock)

    monkeypatch.setattr(attempts_module, "apply_attempt", retire_then_apply)
    return seen


def test_landing_i_a_too_easy_retirement_during_a_session(tmp_path, monkeypatch):
    paths, _vault_loaded, repository = _vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
            "VALUES (?, 'Phone', 'app', 'hash-phone', '2026-10-27T00:00:00Z')", (PHONE,))
        connection.commit()
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    assert repository.fetch_session(session_id)["owner_device_id"] is None  # the desktop

    # The owner's submit passes the acceptance check; the first report follows.
    _submit(ctx, session_id, "pi_diag_easy", 1.0)
    _step()
    _call(ctx, "retire_practice_item", {"practiceItemId": "pi_diag_easy", "reason": "too_easy"})
    _step()
    [first] = _claims(repository)
    assert first["superseded_by"] is None

    # The second report commits inside the second answer's grading window.
    seen = _retire_before_the_attempt_commits(monkeypatch, paths, "pi_diag_mid")
    _submit(ctx, session_id, "pi_diag_mid", 4.0)
    _step()
    assert seen["retired"].active is False
    first, second = _claims(repository)
    assert first["scope_id"] == second["scope_id"] == "lo_diag"
    assert first["superseded_by"] == second["id"] and second["superseded_by"] is None
    state = repository.practice_item_state("pi_diag_mid")
    # mvp-0.37: the attempt kept the retirement's closed row and its hash; its own columns landed.
    assert state.active is False and state.content_hash == seen["retired"].content_hash
    assert state.content_hash == practice_item_hash(load_vault(paths.root).practice_items["pi_diag_mid"])
    assert state.last_attempt_at is not None and state.stability is not None
    assert _shadow_summary(paths)["summary"] == ZERO

    # The phone adopts the session: the desktop's session-scoped submit is
    # refused and writes nothing; its retirement (not session-scoped) lands.
    repository.adopt_session(session_id, PHONE, 0)
    _step()
    attempts, claims = _attempts(repository), _claims(repository)
    with pytest.raises(SidecarError) as moved:
        _submit(ctx, session_id, "pi_diag_hard", 4.0)
    assert moved.value.code == "session_moved"
    assert (_attempts(repository), _claims(repository)) == (attempts, claims)
    _step()
    _call(ctx, "retire_practice_item", {"practiceItemId": "pi_eig_easy", "reason": "too_easy"})
    assert [row["scope_id"] for row in _claims(repository)] == ["lo_diag", "lo_diag", "lo_eigen_basics"]
    assert repository.practice_item_state("pi_eig_easy").active is False

    assert _shadow_summary(paths)["summary"] == ZERO



def test_landing_i_control_below_the_tag_the_same_session_reopens_the_retired_row(tmp_path, monkeypatch):
    """The control: at the kept replaced claims' mvp-0.36 (below PR-4's tag)
    the replace seam is the same, but the attempt's whole-row write reopens
    the row the concurrent retirement closed (PR-2's reverse race, which
    mvp-0.37 closes)."""

    from learnloop.algorithm_versions import SUPERSEDED_CLAIMS_ALGORITHM_VERSION

    paths, _vault_loaded, repository = _vault(tmp_path, version=SUPERSEDED_CLAIMS_ALGORITHM_VERSION)
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _submit(ctx, session_id, "pi_diag_easy", 1.0)
    _step()
    _call(ctx, "retire_practice_item", {"practiceItemId": "pi_diag_easy", "reason": "too_easy"})
    _step()
    seen = _retire_before_the_attempt_commits(monkeypatch, paths, "pi_diag_mid")
    _submit(ctx, session_id, "pi_diag_mid", 4.0)
    assert seen["retired"].active is False
    first, second = _claims(repository)
    assert first["superseded_by"] == second["id"] and second["superseded_by"] is None
    assert repository.practice_item_state("pi_diag_mid").active is True


# -- Interaction (iii): the AD denial-log archival (main 416a9ddfe) at mobile PR-4's upgrade ----------


def _denial_cli(monkeypatch):
    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


@pytest.mark.parametrize("start", ["mvp-0.36", "mvp-0.35"], ids=["direct", "chained-from-mvp-0.35"])
def test_landing_iii_upgrade_to_mvp037_archives_the_denial_log_exactly_once(tmp_path, monkeypatch, start):
    """`upgrade --to mvp-0.37` (directly, or chained from mvp-0.35 through
    mvp-0.36) archives the AD guard's denial log once, after the final step,
    naming the command's start and target; a second, refused run leaves the
    log written since in place."""

    from tests.test_ad_denial_log import OLD_LINE, _archives, _upgrade, _write_log
    from tests.helpers import create_placement_vault
    from learnloop.adaptive_difficulty import denial_log as D
    from learnloop.adaptive_difficulty import operation as O

    _denial_cli(monkeypatch)
    paths = create_placement_vault(tmp_path / "v", version=start)
    log = _write_log(paths, [OLD_LINE, {**OLD_LINE, "table": "mastery_ekf"}])
    before = log.read_text(encoding="utf-8")
    result = _upgrade(paths, LATEST_ALGORITHM_VERSION)
    assert result.exit_code == 0, result.output
    assert f"{start} -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.38"
    [archive] = _archives(paths)
    assert archive.name.startswith(f"ad_guard_denials.archived-{start}-to-{LATEST_ALGORITHM_VERSION}-")
    assert archive.read_text(encoding="utf-8") == before and not log.exists()
    assert result.output.count("AD guard denial log archived") == 1
    assert O.denial_count(paths.sqlite_path) == 0 and D.summary(paths.sqlite_path)["archived_denials"] == 2

    # Refused (already at the tag): the log written since stays live and nothing more is archived.
    log = _write_log(paths, [OLD_LINE])
    again = _upgrade(paths, LATEST_ALGORITHM_VERSION)
    assert again.exit_code == 1 and f"vault is already {LATEST_ALGORITHM_VERSION}" in again.output, again.output
    assert log.exists() and _archives(paths) == [archive] and O.denial_count(paths.sqlite_path) == 1


def test_landing_iii_a_refused_chained_upgrade_to_mvp037_leaves_the_log_in_place(tmp_path, monkeypatch):
    """A chain the first link refuses (a vault older than the chain) archives nothing."""

    from tests.test_ad_denial_log import OLD_LINE, _archives, _upgrade, _write_log
    from tests.helpers import create_placement_vault

    _denial_cli(monkeypatch)
    paths = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    log = _write_log(paths, [OLD_LINE])
    result = _upgrade(paths, LATEST_ALGORITHM_VERSION)
    assert result.exit_code == 1, result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    assert log.exists() and _archives(paths) == []
