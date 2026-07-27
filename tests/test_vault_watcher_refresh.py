from __future__ import annotations

from pathlib import Path

from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext

from tests.helpers import create_basic_vault

ITEM = "pi_svd_define_001"


def test_practice_item_watch_refresh_is_incremental(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    context = SidecarContext()
    context.load(root, maintenance=False)
    vault, repository = context.require_vault()
    before_revision = repository.queue_revision()["revision"]
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    payload = vault.practice_items[ITEM].model_dump(mode="json", exclude_none=False)
    payload["prompt"] = "Define the singular value decomposition."
    upsert_practice_item(root, payload, loaded_vault=vault)

    def unexpected_reload(*_args, **_kwargs):
        raise AssertionError("Practice Item refresh must stay incremental")

    monkeypatch.setattr(context, "reload", unexpected_reload)
    result = context.refresh_vault_files(
        [item_path.relative_to(root).as_posix()],
        expected_root=root,
    )

    assert result["mode"] == "incremental"
    assert result["changed_practice_item_ids"] == [ITEM]
    assert context.require_vault()[0].practice_items[ITEM].prompt == payload["prompt"]
    assert result["queue_revision"] == before_revision + 1


def test_watch_refresh_rejects_an_event_from_the_previously_selected_vault(
    tmp_path: Path,
) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    context = SidecarContext()
    context.load(root, maintenance=False)
    item_path = paths.practice_item_path("linear-algebra", ITEM)

    result = context.refresh_vault_files(
        [item_path.relative_to(root).as_posix()],
        expected_root=tmp_path / "different-vault",
    )

    assert result["mode"] == "stale"
    assert result["changed_practice_item_ids"] == []


def test_practice_item_deletion_deactivates_cached_serving_state(
    tmp_path: Path,
) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    context = SidecarContext()
    context.load(root, maintenance=False)
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    item_path.unlink()

    result = context.refresh_vault_files(
        [item_path.relative_to(root).as_posix()],
        expected_root=root,
    )

    vault, repository = context.require_vault()
    assert result["mode"] == "incremental"
    assert ITEM not in vault.practice_items
    assert repository.practice_item_state(ITEM).active is False


def test_non_item_watch_refresh_returns_the_updated_application_snapshot(
    tmp_path: Path,
) -> None:
    root = tmp_path / "vault"
    create_basic_vault(root)
    context = SidecarContext()
    context.load(root, maintenance=False)

    result = context.refresh_vault_files(
        ["learnloop.toml"],
        expected_root=root,
    )

    assert result["mode"] == "full"
    assert result["snapshot"]["vault"]["root"] == str(root.resolve())
