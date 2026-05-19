from __future__ import annotations

import os
from pathlib import Path

# Relocate pytest's temp root into the repo. The default location under the
# user's AppData/Local/Temp can be unwritable on some Windows setups, which
# makes every test that uses tmp_path error during setup. Pointing the root at
# a repo-local, gitignored directory is portable and side-effect free.
_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".pytest_tmp"
_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMP_ROOT))
