"""The desks' client model and the sidecar agree op for op (spec §3.4).

The client applies `desk.apply` ops to its own workspace model before the server answers
(apps/learnloop-tauri/src/screens/desks/model/workspace.ts), so its layout must be the one the server
stores. One script, `apps/learnloop-tauri/src/fixtures/desks/opParity.json`, is run here through the
sidecar's ops and in `opParity.test.ts` through the client model: both must give its results and its
final state."""

from __future__ import annotations

import json
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.desks.workspace import desk_state
from tests.desk_helpers import Batches
from tests.helpers import create_basic_vault

SCRIPT = Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "fixtures" / "desks" / "opParity.json"


def test_the_sidecar_gives_the_scripts_results_and_final_state(tmp_path):
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    repository = Repository(create_basic_vault(tmp_path / "vault").sqlite_path)
    batches = Batches(repository)
    results = [[result["status"] for result in batches.desk(*ops)["results"]] for ops in script["batches"]]
    assert results == script["results"]
    final = [
        {
            "deskId": desk["desk_id"],
            "title": desk["title"],
            "focusWindowId": desk["focus_window_id"],
            "version": desk["version"],
            "slots": [[[window["window_id"], window["active"]] for window in slot["windows"]] for slot in desk["slots"]],
        }
        for desk in desk_state(repository)["desks"]
    ]
    assert final == script["final"]
