"""Take one UX walk down: its driver (and Chromium, chromedriver) and its bridge (and the sidecar).

    python scripts/ux_walk/stop.py <walk-name> [--walks-dir fixtures-local/ux-walks]

Stops exactly the two scope units start.py named for this walk, after
recording what each used (``analyst/memory.json``: current and peak memory
per unit, from systemd). The walk's files stay for the analyst.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WALKS = ROOT / "fixtures-local" / "ux-walks"


SYSTEMD_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"}


def unit_memory(unit: str) -> dict:
    result = subprocess.run(["systemctl", "--user", "show", f"{unit}.scope", "-p", "MemoryCurrent",
                             "-p", "MemoryPeak", "-p", "ActiveState"], capture_output=True, text=True,
                            env=SYSTEMD_ENV)
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    out: dict[str, object] = {"state": values.get("ActiveState")}
    for key in ("MemoryCurrent", "MemoryPeak"):
        raw = values.get(key, "")
        out[key] = round(int(raw) / 2**20) if raw.isdigit() else None
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("name")
    parser.add_argument("--walks-dir", default=str(DEFAULT_WALKS))
    args = parser.parse_args(argv)
    walk_root = Path(args.walks_dir).resolve() / args.name
    record_path = walk_root / "run" / "walk.json"
    units = (json.loads(record_path.read_text(encoding="utf-8"))["units"] if record_path.exists()
             else [f"uxwalk-{args.name}-driver", f"uxwalk-{args.name}-bridge"])
    memory = {unit: unit_memory(unit) for unit in units}
    if (walk_root / "analyst").exists():
        (walk_root / "analyst" / "memory.json").write_text(json.dumps(memory, indent=2), encoding="utf-8")
    # The driver first, so the browser never outlives the server it is talking to.
    for unit in sorted(units, key=lambda name: 0 if name.endswith("-driver") else 1):
        subprocess.run(["systemctl", "--user", "stop", f"{unit}.scope"], capture_output=True, env=SYSTEMD_ENV)
    time.sleep(0.5)
    left = {unit: unit_memory(unit)["state"] for unit in units}
    print(json.dumps({"memory_mb": memory, "after_stop": left}, indent=2))
    return 0 if all(state in ("inactive", None, "") for state in left.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
