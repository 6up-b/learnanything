"""Learner item-authoring sidecar RPCs (author/edit/retire/split) over serve()."""

from __future__ import annotations

import io
import json
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
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
