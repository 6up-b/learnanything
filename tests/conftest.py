from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# On Windows only: relocate pytest's temp root into the repo. The default
# location under the user's AppData/Local/Temp can be unwritable on some
# Windows setups, which makes every test that uses tmp_path error during
# setup. Everywhere else the OS temp dir must be used as-is — on Linux it is
# typically tmpfs, and a repo-local root would put every per-test sqlite
# vault on the project filesystem, where fsync-heavy commits dominate the
# suite (measured ~9s/test on btrfs vs ~30ms on tmpfs).
if sys.platform == "win32":
    _TEMP_ROOT = Path(__file__).resolve().parent.parent / ".pytest_tmp"
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMP_ROOT))
else:
    _TEMP_ROOT = Path(tempfile.gettempdir()) / "learnloop_pytest"
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

# Isolate tests from machine-global learnloop settings. Point LEARNLOOP_CONFIG_DIR
# at an empty dir (so a developer's real ~/.config/learnloop/settings.env is not
# read) and clear LEARNLOOP_CODEX_CHECKOUT_PATH, so per-test fixtures that inject
# a temp Codex checkout/revision are not overridden by the ambient environment.
os.environ["LEARNLOOP_CONFIG_DIR"] = str(_TEMP_ROOT / "global_settings_isolated")
os.environ.pop("LEARNLOOP_CODEX_CHECKOUT_PATH", None)
