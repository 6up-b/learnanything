"""Learner item-authoring sidecar RPCs (author/edit/retire/split) over serve()."""

from __future__ import annotations

import io
import json
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault, seed_due_item

ITEM = "pi_svd_define_001"


def _rpc(root: Path, calls: list[tuple[str, dict]]) -> list[dict]:
    messages = [{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"vaultPath": str(root)}}]
    for i, (method_name, params) in enumerate(calls, start=1):
        messages.append({"jsonrpc": "2.0", "id": i, "method": method_name, "params": params})
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_edit_retire_author_flow(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths)
    vault = load_vault(root)
    lo_id = next(iter(vault.learning_objects))

    out = _rpc(root, [
        ("edit_practice_item", {"practiceItemId": ITEM, "prompt": "Sharper prompt?"}),
        ("retire_practice_item", {"practiceItemId": ITEM, "reason": "knew_prompt_not_concept", "note": "parroting"}),
        ("author_practice_item", {
            "learningObjectId": lo_id,
            "prompt": "State the shapes in a thin SVD of an m x n matrix.",
            "expectedAnswer": "U: m x r, S: r x r, V: n x r.",
        }),
        ("retire_practice_item", {"practiceItemId": ITEM, "reason": "not_a_reason"}),
    ])

    assert out[1]["result"]["changed"] == ["prompt"]
    assert out[2]["result"]["status"] == "retired"
    new_id = out[3]["result"]["practiceItemId"]
    assert new_id.startswith("pi_learner_")
    assert out[4]["error"]["data"]["code"] == "validation_error"

    reloaded = load_vault(root)
    assert reloaded.practice_items[ITEM].status == "retired"
    assert reloaded.practice_items[ITEM].prompt == "Sharper prompt?"
    assert reloaded.practice_items[new_id].status == "active"
    # The reload inside the handler ran state_sync: retired item deactivated.
    repo = Repository(paths.sqlite_path)
    states = repo.practice_item_states()
    assert not states[ITEM].active
    assert states[new_id].active


def test_split_flow(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths)

    out = _rpc(root, [
        ("split_practice_item", {
            "practiceItemId": ITEM,
            "parts": [
                {"prompt": "What does SVD factor A into?", "expectedAnswer": "U S V^T"},
                {"prompt": "What lives on S's diagonal?", "expectedAnswer": "Singular values"},
            ],
        }),
    ])
    created = out[1]["result"]["created"]
    assert len(created) == 2
    reloaded = load_vault(root)
    assert reloaded.practice_items[ITEM].status == "retired"
    for new_id in created:
        assert reloaded.practice_items[new_id].status == "active"


def test_retire_rpc_updates_cached_vault_without_global_reload(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = seed_due_item(paths)
    session_id = repository.create_session(energy="medium", available_minutes=25)

    def unexpected_reload(*_args, **_kwargs):
        raise AssertionError("retirement must not trigger a global vault reload")

    monkeypatch.setattr(SidecarContext, "reload", unexpected_reload)
    out = _rpc(
        root,
        [
            (
                "retire_practice_item",
                {"practiceItemId": ITEM, "reason": "no_longer_relevant"},
            ),
            ("get_today_queue", {"availableMinutes": 25}),
            ("open_queue_item", {"practiceItemId": ITEM}),
            (
                "save_practice_draft",
                {
                    "sessionId": session_id,
                    "practiceItemId": ITEM,
                    "answerMd": "late autosave",
                },
            ),
            (
                "submit_dont_know",
                {"sessionId": session_id, "practiceItemId": ITEM},
            ),
        ],
    )

    assert out[1]["result"]["status"] == "retired"
    assert isinstance(out[1]["result"]["queueRevision"], int)
    assert out[2]["result"]["totalItems"] == 0
    assert out[3]["error"]["data"]["code"] == "item_retired"
    assert out[4]["error"]["data"]["code"] == "item_retired"
    assert out[5]["error"]["data"]["code"] == "item_retired"
    assert repository.fetch_session_checkpoint(session_id) is None
