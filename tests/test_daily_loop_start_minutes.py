"""Daily-loop DL0: start friction (``docs/specs/spec_daily_loop_v1.md`` §12 row DL0).

- §6.6 (P4): no readiness form. Start asks for minutes only, remembers the last
  session's (25 on a fresh vault, D1), and changes them with one tap.
  ``start_session`` still accepts energy and sleep for old clients and the CLI.
- §6.5 (P2): Next on feedback opens the head of the live queue; Esc keeps the
  list. The desktop half is ``apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx``;
  the TUI half is here.
- §8 (D8) and gate G11: the streak's count is unchanged (local days with a
  started session), and any client's session row counts. The desktop label is
  covered by ``apps/learnloop-tauri/src/screens/StartScreen.test.tsx``.
- DL0 changes nothing served: ``get_today_queue`` on copies of the tracked
  fixture vaults serves the same queue whether or not energy is sent.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.scheduling.session_minutes import (
    FIRST_RUN_MINUTES,
    MINUTE_PRESETS,
    minute_choices,
    remembered_session_minutes,
)
from learnloop.tui import screens as tui_screens
from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.tui.screens.practice import PracticeScreen
from learnloop.tui.screens.start import MinutesPicker, StartScreen
from learnloop.tui.screens.today import TodayScreen
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import add_followup_item, begin_session, create_basic_vault, seed_due_item

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WORKING_FIXTURES = ("linear_algebra", "probability", "arxiv_v2")
SECOND_ITEM = "pi_svd_define_002"


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(vault_root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(vault_root)
    ctx.grading_provider_override = "manual"
    return ctx


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── §6.6: minutes only, remembered ─────────────────────────────────────────


def test_start_session_needs_no_energy_or_sleep_and_still_accepts_them(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = _context(paths.root)

    session = _call(ctx, "start_session", {"availableMinutes": 40})
    assert session["availableMinutes"] == 40
    assert session["energy"] is None
    assert session["sleepQuality"] is None
    row = Repository(paths.sqlite_path).fetch_session(session["sessionId"])
    assert (row["energy"], row["sleep_quality"], row["available_minutes"]) == (None, None, 40)

    # Old clients and the CLI may still send them; nothing rejects them.
    legacy = _call(ctx, "start_session", {"energy": "high", "sleepQuality": 0.4, "availableMinutes": 30})
    assert (legacy["energy"], legacy["sleepQuality"]) == ("high", 0.4)


def test_start_summary_remembers_the_last_sessions_minutes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = _context(paths.root)

    first_run = _call(ctx, "get_start_summary", {})
    assert first_run["rememberedMinutes"] == FIRST_RUN_MINUTES == 25
    assert first_run["minutesSource"] == "first_run"
    assert first_run["minutesPresets"] == [10, 15, 25, 40, 60] == list(MINUTE_PRESETS)
    assert first_run["minuteChoices"] == [10, 15, 25, 40, 60]
    assert first_run["streak"] == {"current": 0, "activeToday": False, "longest": 0}

    _call(ctx, "start_session", {"availableMinutes": 40})
    assert _call(ctx, "get_start_summary", {})["rememberedMinutes"] == 40
    _call(ctx, "start_session", {"availableMinutes": 15})
    after_chip = _call(ctx, "get_start_summary", {})
    assert (after_chip["rememberedMinutes"], after_chip["minutesSource"]) == (15, "last_session")

    # A session that recorded no minutes (an old client) does not erase them.
    _call(ctx, "start_session", {})
    assert _call(ctx, "get_start_summary", {})["rememberedMinutes"] == 15

    # A budget from the old chips stays a visible choice rather than snapping.
    _call(ctx, "start_session", {"availableMinutes": 30})
    legacy_budget = _call(ctx, "get_start_summary", {})
    assert legacy_budget["rememberedMinutes"] == 30
    assert legacy_budget["minuteChoices"] == [10, 15, 25, 30, 40, 60]
    assert legacy_budget["streak"]["activeToday"] is True


def test_start_summary_is_a_read(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = _context(paths.root)
    _call(ctx, "start_session", {"availableMinutes": 40})
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        before = [tuple(row) for row in connection.execute("SELECT * FROM sessions ORDER BY id")]
    for _ in range(3):
        _call(ctx, "get_start_summary", {})
    with repository.connection() as connection:
        after = [tuple(row) for row in connection.execute("SELECT * FROM sessions ORDER BY id")]
    assert after == before


def test_remembered_minutes_follow_session_start_order(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    base = datetime(2026, 10, 1, 9, tzinfo=UTC)
    # Inserted out of order: the latest *start* wins, not the latest insert.
    repository.create_session(available_minutes=60, clock=FrozenClock(base + timedelta(days=2)))
    repository.create_session(available_minutes=10, clock=FrozenClock(base))
    repository.create_session(available_minutes=None, clock=FrozenClock(base + timedelta(days=3)))
    remembered = remembered_session_minutes(repository)
    assert (remembered.minutes, remembered.source) == (60, "last_session")
    assert minute_choices(60) == (10, 15, 25, 40, 60)
    assert minute_choices(45) == (10, 15, 25, 40, 45, 60)


# ── §8 and G11: the streak ─────────────────────────────────────────────────


def _streak_by_definition(repository: Repository, today: date) -> dict:
    """An independent reading of §8: local calendar days on which a session started."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT date(started_at, 'localtime') AS day FROM sessions WHERE started_at IS NOT NULL"
        ).fetchall()
    days = {date.fromisoformat(row["day"]) for row in rows}
    if not days:
        return {"current": 0, "active_today": False, "longest": 0}
    cursor = today if today in days else today - timedelta(days=1)
    current = 0
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    longest = 0
    for day in days:
        if day - timedelta(days=1) in days:
            continue
        run = 1
        while day + timedelta(days=run) in days:
            run += 1
        longest = max(longest, run)
    return {"current": current, "active_today": today in days, "longest": longest}


def test_the_streak_counts_any_clients_started_sessions(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    today = datetime.now(UTC).astimezone().replace(hour=12, minute=0, second=0, microsecond=0)
    # Desktop sessions two and three days ago, with the old readiness inputs.
    for days_ago in (3, 2):
        repository.create_session(
            energy="medium", sleep_quality=0.5, available_minutes=30,
            clock=FrozenClock((today - timedelta(days=days_ago)).astimezone(UTC)),
        )
    # Yesterday: a row as another client writes it (mobile M2 sessions are rows
    # in `sessions` too), with no minutes and no readiness inputs at all.
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, energy, sleep_quality, available_minutes, notes_md_path, updated_at) "
            "VALUES ('phone-session-1', ?, NULL, NULL, NULL, NULL, NULL, ?)",
            (_iso(today - timedelta(days=1)), _iso(today - timedelta(days=1))),
        )
        connection.commit()

    clock = FrozenClock(today.astimezone(UTC))
    before_today = repository.session_day_streak(clock=clock)
    assert before_today == {"current": 3, "active_today": False, "longest": 3}
    assert before_today == _streak_by_definition(repository, today.date())

    # Beginning a session today is what keeps it: a DL0 start sends minutes only.
    repository.create_session(available_minutes=25, clock=clock)
    kept = repository.session_day_streak(clock=clock)
    assert kept == {"current": 4, "active_today": True, "longest": 4}
    assert kept == _streak_by_definition(repository, today.date())


@pytest.mark.parametrize("fixture_name", WORKING_FIXTURES)
def test_the_streak_count_is_unchanged_on_fixture_copies(tmp_path, fixture_name):
    source = FIXTURES / fixture_name
    if not (source / "state.sqlite").exists():
        pytest.skip(f"{fixture_name} fixture absent")
    root = tmp_path / fixture_name
    copy_tree_with_databases(source, root)
    repository = Repository(root / "state.sqlite")
    with repository.connection() as connection:
        latest = connection.execute("SELECT MAX(started_at) AS latest FROM sessions").fetchone()["latest"]
    if latest is None:
        # A fixture with no session history has no streak, by either reading.
        moments = [datetime(2026, 10, 12, 12, tzinfo=UTC).astimezone()]
    else:
        last_day = clock_module.parse_utc(latest).astimezone()
        moments = [last_day, last_day + timedelta(days=1), last_day + timedelta(days=2)]
    for moment in moments:
        streak = repository.session_day_streak(clock=FrozenClock(moment.astimezone(UTC)))
        assert streak == _streak_by_definition(repository, moment.date())

    # The start summary reports the same streak the vault load does.
    ctx = _context(root)
    assert _call(ctx, "get_start_summary", {})["streak"] == ctx.app_snapshot()["streak"]


# ── Nothing served changes ─────────────────────────────────────────────────

_VOLATILE = {"schedulerSlateId", "schedulerCandidateId", "generatedAt", "readinessFactor"}


def _served(value):
    if isinstance(value, dict):
        return {key: _served(item) for key, item in value.items() if key not in _VOLATILE}
    if isinstance(value, list):
        return [_served(item) for item in value]
    return value


@pytest.mark.parametrize("fixture_name", WORKING_FIXTURES)
def test_today_queue_serves_the_same_queue_without_energy_on_fixture_copies(tmp_path, monkeypatch, fixture_name):
    """Start stops sending energy: the queue served is the same item for item.

    Only the logged ``readinessFactor`` moves (it never reaches priority, spec
    §3.1). The clock is frozen because forgetting risk decays continuously.
    """

    source = FIXTURES / fixture_name
    if not (source / "state.sqlite").exists():
        pytest.skip(f"{fixture_name} fixture absent")
    root = tmp_path / fixture_name
    copy_tree_with_databases(source, root)
    frozen = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda self: frozen)
    ctx = _context(root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]

    def queue(**extra):
        return _call(ctx, "get_today_queue", {"sessionId": session_id, "availableMinutes": 25, **extra})

    before_dl0 = queue(energy="medium")
    after_dl0 = queue()
    assert before_dl0["totalItems"] > 0
    assert _served(after_dl0) == _served(before_dl0)
    for energy in ("low", "high"):
        assert _served(queue(energy=energy)) == _served(before_dl0)
    assert {item["readinessFactor"] for section in after_dl0["sections"] for item in section["items"]} == {1.0}


# ── The TUI: minutes-only Start and auto-advance ───────────────────────────


def test_tui_start_asks_for_minutes_only_and_starts_on_the_remembered_minutes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    Repository(paths.sqlite_path).create_session(available_minutes=40)

    async def scenario() -> None:
        app = LearnLoopApp(paths.root)
        async with app.run_test(size=(160, 50)) as pilot:
            await pilot.pause()
            start = app.screen
            assert isinstance(start, StartScreen)
            assert not start.query("#energy") and not start.query("#sleep")
            assert not hasattr(tui_screens.start, "Slider")
            picker = start.query_one("#minutes", MinutesPicker)
            assert picker.minutes == 40
            assert picker.choices == (10, 15, 25, 40, 60)
            assert "minutes from your last session" in str(start.query_one("#warmup-intro").render())

            sessions = []
            refresh = app.state.refresh
            app.state.refresh = lambda *, session=None: (sessions.append(session), refresh(session=session))[1]

            # One tap on a chip: " 10m " then a space, so " 15m " spans columns 6-10.
            await pilot.click("#minutes", offset=(7, 0))
            assert picker.minutes == 15
            await pilot.press("right", "right", "right")  # 15 -> 25 -> 40 -> 60
            assert picker.minutes == 60
            today = await begin_session(app, pilot)
            assert isinstance(today, TodayScreen)
            assert sessions[0].available_minutes == 60
            assert sessions[0].energy is None
            assert app.state.available_minutes == 60
            assert "60 min budget" in str(today.query_one("#today-summary").render())

    asyncio.run(scenario())


def test_tui_start_uses_25_minutes_on_a_fresh_vault_and_keeps_an_old_budget(tmp_path):
    fresh = create_basic_vault(tmp_path / "fresh")
    old = create_basic_vault(tmp_path / "old")
    Repository(old.sqlite_path).create_session(available_minutes=30)

    async def picker_for(root: Path) -> tuple[int, tuple[int, ...]]:
        app = LearnLoopApp(root)
        async with app.run_test() as pilot:
            await pilot.pause()
            picker = app.screen.query_one("#minutes", MinutesPicker)
            return picker.minutes, picker.choices

    assert asyncio.run(picker_for(fresh.root)) == (25, (10, 15, 25, 40, 60))
    assert asyncio.run(picker_for(old.root)) == (30, (10, 15, 25, 30, 40, 60))


def test_tui_start_lays_the_minute_chips_out_on_screen(tmp_path):
    """Start's stylesheet applies (Textual never loads a default screen's own
    CSS_PATH), so the chips, Start's only control, are visible and whole."""

    paths = create_basic_vault(tmp_path / "vault")

    async def scenario() -> None:
        app = LearnLoopApp(paths.root)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            start = app.screen
            picker = start.query_one("#minutes", MinutesPicker)
            assert start.query_one("#minutes-row").region.height == 1
            assert start.query_one("#minutes-label").region.width == 16
            assert start.region.contains_region(picker.region)
            chips_width = sum(len(f" {m}m ") for m in picker.choices) + len(picker.choices) - 1
            assert picker.region.width >= chips_width

    asyncio.run(scenario())


def _two_due_items(tmp_path: Path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    return paths


async def _graded_feedback(app, pilot) -> FeedbackScreen:
    today = await begin_session(app, pilot)
    await today.open_practice()
    await pilot.pause()
    practice = app.screen
    assert isinstance(practice, PracticeScreen)
    practice.set_answer("A factorization into U, Sigma, V transpose.")
    feedback = await practice.open_feedback()
    await pilot.pause()
    feedback.set_points("correctness", 4)
    feedback.set_confidence(5)
    feedback.submit()
    await pilot.pause()
    return feedback


def test_tui_next_opens_the_head_of_the_live_queue(tmp_path):
    paths = _two_due_items(tmp_path)

    async def scenario() -> None:
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            feedback = await _graded_feedback(app, pilot)
            feedback.action_next()
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, PracticeScreen)
            today = next(screen for screen in app.screen_stack if isinstance(screen, TodayScreen))
            # The head of the queue rebuilt after the attempt, as Today shows it.
            assert today._items, "the rebuilt queue still has work"
            assert app.screen.item.practice_item_id == today._items[0].practice_item_id
            assert today.open_head_on_resume is False

    asyncio.run(scenario())


def test_tui_esc_keeps_the_list_and_an_ungraded_next_returns_to_it(tmp_path):
    paths = _two_due_items(tmp_path)

    async def scenario() -> None:
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            feedback = await _graded_feedback(app, pilot)
            feedback.action_back()
            await pilot.pause()
            assert isinstance(app.screen, TodayScreen)

            await app.screen.open_practice()
            await pilot.pause()
            ungraded = await app.screen.open_feedback()
            await pilot.pause()
            ungraded.action_next()
            await pilot.pause()
            assert isinstance(app.screen, TodayScreen)

    asyncio.run(scenario())
