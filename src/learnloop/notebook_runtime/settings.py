"""The notebook runtime's named settings that are not vault config.

The owner was asked six questions after the gate (``docs/reviews/notebook-na0.2.md``, "Owner decisions"); until the
answers come, each default is one name: here, in ``NotebooksConfig`` (memory, idle minutes, sessions, scratch size)
or, for the frame origins, in the app's CSP (``frame-src http://127.0.0.1:*`` in ``tauri.conf.json``).
"""
from __future__ import annotations

#: Owner decision 3 (default while asked): cells the learner writes run in the same sandbox as model-written ones.
#: There is no unsandboxed runtime; a False here is refused, not honoured.
LEARNER_CELLS_SANDBOXED = True
#: Owner decision 6 (default while asked): CPU only. No GPU device node enters the sandbox; the profile's ``/dev``
#: has none, and passing ``/dev/nvidia*`` or ``/dev/dri`` to model-written code is not built.
CPU_ONLY = True

#: The proxy binds here and nowhere else; the app's CSP allows framing any port on it (owner decision 1's default).
FRAME_HOST = "127.0.0.1"
#: The documents allowed to frame a notebook (its CSP's ``frame-ancestors``) and to receive its bridge messages:
#: the app's own document on Linux and macOS, on Windows, and the development server.
WORKBENCH_ORIGINS: tuple[str, ...] = ("tauri://localhost", "http://tauri.localhost", "https://tauri.localhost",
                                      "http://localhost:1420")

# keep (machine safety): the scope's caps besides memory, the figure renders' values.
CPU_QUOTA = "200%"
TASKS_MAX = 512

# keep (guardrails, not parameters): how long the supervisor waits, and how often it restarts.
READY_TIMEOUT_SECONDS = 60.0
STOP_TIMEOUT_SECONDS = 10.0
RESTART_LIMIT = 3
RESTART_BACKOFF_SECONDS = 0.5
#: How often idle sessions are checked.
SWEEP_SECONDS = 30.0
#: The largest notebook file a session is opened on.
NOTEBOOK_MAX_BYTES = 2 * 1024 * 1024
# keep (machine safety): the frame's requests and the UI values the proxy keeps for replay live in the sidecar's
# memory, outside the session's caps, so each is bounded by the size of the notebook itself.
REQUEST_MAX_BYTES = NOTEBOOK_MAX_BYTES
UI_VALUES_MAX_BYTES = NOTEBOOK_MAX_BYTES
