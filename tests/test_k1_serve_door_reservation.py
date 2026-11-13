"""K1-3: the session serve door refuses an item reserved for a goal's held-out exam."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.serving import refuse_held_out_item
from tests.helpers import create_basic_vault


@pytest.fixture
def served(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    return vault, Repository(paths.sqlite_path), next(iter(vault.practice_items.values()))


def _reserve(monkeypatch, *item_ids):
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: set(item_ids))


def test_a_reserved_item_is_refused_at_the_session_serve_door(served, monkeypatch):
    vault, repository, item = served
    _reserve(monkeypatch, item.id)
    with pytest.raises(SidecarError) as caught:
        refuse_held_out_item(vault, repository, item)
    assert caught.value.code == "exam_reserved"
    assert caught.value.details == {"practice_item_id": item.id}


def test_the_reservation_refusal_does_not_follow_the_held_out_selection_switch(served, monkeypatch):
    import learnloop_sidecar.serving as serving

    vault, repository, item = served
    _reserve(monkeypatch, item.id)
    monkeypatch.setattr(serving, "held_out_selection_active", lambda _vault: False)
    with pytest.raises(SidecarError):
        refuse_held_out_item(vault, repository, item)


def test_an_unreserved_item_is_served(served, monkeypatch):
    vault, repository, item = served
    _reserve(monkeypatch)
    refuse_held_out_item(vault, repository, item)
