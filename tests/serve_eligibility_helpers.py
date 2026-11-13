"""What other test files use from ``tests/test_serve_eligibility.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.version_floor import is_below_floor

from tests.helpers import allow_below_floor


START = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
SUCCESSOR = "mvp-0.27"


def _iso(moment: datetime) -> str:
    return utc_now_iso(FrozenClock(moment))


def _at_version(root, version: str = SUCCESSOR, *, enabled: bool = True) -> None:
    """Pin a test vault's ``algorithm_version`` (the basic vault is mvp-0.6,
    the daily-plan vault mvp-0.14) and, optionally, turn the switch off."""

    import re

    toml = root / "learnloop.toml"
    text, count = re.subn(r'algorithm_version = "[^"]+"', f'algorithm_version = "{version}"', toml.read_text(), count=1)
    assert count == 1
    if not enabled:
        text += "\n[eligibility]\nenabled = false\n"
    toml.write_text(text)
    if is_below_floor(version):
        allow_below_floor(root)


def _repair(tmp_path, version: str = SUCCESSOR, *, enabled: bool = True):
    """``test_remediation_cold_retry._setup`` at ``version``."""

    from learnloop.vault.loader import load_vault
    from tests.remediation_cold_retry_helpers import _setup

    vault, repository, misconception_id = _setup(tmp_path)
    _at_version(vault.root, version, enabled=enabled)
    return load_vault(vault.root), repository, misconception_id


def _basic(tmp_path, version: str = SUCCESSOR, *, enabled: bool = True):
    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    _at_version(paths.root, version, enabled=enabled)
    return paths


def _one_cold_item_plan(
    tmp_path, *, reveal_kind: str = "tutor_answer", reveal_ago=timedelta(hours=26), start=START,
    version: str = SUCCESSOR, enabled: bool = True,
):
    """§12.9's reproduction (``test_f1k_a_non_routine_reveal_never_starves_the_plan``'s
    setup): one eligible item, a cold retry created a day ago and due for an
    hour, and a non-routine reveal of the item made before the task."""

    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_c": [("pi_cold", 1.0)]})
    _at_version(paths.root, version, enabled=enabled)
    clock = MovableClock(start)
    env = make_env(paths.root, [scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry")],
                   clock=clock, session_id="s_one")
    seed_due(env.repository, "pi_cold", due=start - timedelta(days=2), last=start - timedelta(days=9))
    task = env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_one",
        not_before=_iso(start - timedelta(hours=1)), expires_at=_iso(start + timedelta(days=30)),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": reveal_kind,
         "amount": 1.0, "basis": reveal_kind},
        clock=FrozenClock(start - reveal_ago),
    )
    return env, clock, task
