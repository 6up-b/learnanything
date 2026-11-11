"""What other test files use from ``tests/test_ad_guard.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _slot_serve(tmp_path, monkeypatch, *, plant: bool):
    """One plan serve; with ``plant`` AD's request builder (phase 3, inside its operation) first reads
    ``practice_attempts`` raw on the serve's pinned connection."""

    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import advance, build_plan

    from tests.ad23_fakes import ad23_vault, env_for, selections

    items = ("pi_e1", "pi_e2", "pi_e3")
    paths = ad23_vault(tmp_path, items=items, config="[router]\nenabled = false\n")
    env, _clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    if plant:
        real = ad_slot._request

        def planted(vault, repository, *args, **kwargs):
            repository.connection().execute("SELECT * FROM practice_attempts").fetchall()
            return real(vault, repository, *args, **kwargs)

        monkeypatch.setattr(ad_slot, "_request", planted)
    _record, step = advance(env, serve=True)
    return paths, step, selections(paths, kind="serve")
