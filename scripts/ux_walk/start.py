"""Bring up one UX walk: vault, bridge (sidecar inside), browser bundle, Chromium and the walk driver.

    python scripts/ux_walk/start.py <walk-name> --from established|fresh|empty [--brief brief.md]
        [--files a.pdf b.html] [--phone] [--walks-dir fixtures-local/ux-walks] [--anchor YYYY-MM-DD]
        [--models live --allow-live-route --config-dir <dir> [--decider perplexity]]

Creates ``<walks-dir>/<walk-name>/`` with:

- ``persona/``: the only directory the persona agent gets: ``brief.md``, ``walk``
  (the command), ``files/`` (this person's files for `walk upload`),
  ``observations/`` and ``channel/`` (the file protocol);
- ``vault/``: the walk's own synthetic vault (make_vault.py);
- ``analyst/``: steps, console errors, every bridge call and fake-model request, the
  memory each part used: never shown to the persona;
- ``run/``: the processes' own homes, config, caches and ready files.

Each long-running part runs in its own ``systemd-run --user --scope`` unit
(``uxwalk-<name>-bridge``, ``uxwalk-<name>-driver``) capped at 3 GB, so
stop.py takes down exactly what this started. Model routes are faked; see
README.md for a walk on the owner's ChatGPT-plan route.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TAURI = ROOT / "apps" / "learnloop-tauri"
DEFAULT_WALKS = ROOT / "fixtures-local" / "ux-walks"
SAMPLES = ROOT / "samples"
PHONE_APP_INDEX = ROOT / "src" / "learnloop_mobile" / "static" / "app" / "index.html"
SCOPE = ["-p", "MemoryMax=3G", "-p", "MemorySwapMax=1G"]
PLACEHOLDER_BRIEF = """# Your brief

You are using LearnLoop, a study app, on your computer. Use only what you see on the screen.

Run `./walk look` to see the screen, then act with `./walk click`, `./walk type` and the other
verbs (`./walk help`). Your own files are in files/. Say what you expect, what confuses you and
where you get stuck with `./walk say "..."` as you go.
"""


def default_files(samples: Path | None = None) -> list[Path]:
    """Every sample document (everything under samples/ but its NOTICE), so a brief can name any of them."""

    samples = samples or SAMPLES
    return sorted(path for path in samples.rglob("*") if path.is_file() and path.name != "NOTICE")


def phone_app_refusal(index: Path | None = None) -> str | None:
    """Why a phone walk cannot start, or None: the phone host serves a built app, else a not_found page."""

    index = index or PHONE_APP_INDEX
    if index.is_file():
        return None
    return (f"the phone app is not built ({index.relative_to(ROOT) if index.is_relative_to(ROOT) else index} is "
            "missing): run `npm ci` and then `npm run build` in apps/learnloop-mobile, then start the walk again")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def clean_env(walk_root: Path) -> dict[str, str]:
    home = walk_root / "run" / "home"
    home.mkdir(parents=True, exist_ok=True)
    (walk_root / "run" / "config").mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8",
            "LEARNLOOP_CONFIG_DIR": str(walk_root / "run" / "config")}


def systemd_env() -> dict[str, str]:
    """Enough for ``systemd-run --user`` to reach the user manager; the command itself gets ``env -i``."""

    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"}


def scoped(unit: str | None, command: list[str], env: dict[str, str], *, wait: bool, log: Path,
           cwd: Path = ROOT) -> subprocess.Popen:
    """``command`` inside its own user scope (named ``unit`` when given), in the clean environment."""

    prefix = ["systemd-run", "--user", "--scope", "-q", *SCOPE]
    if unit:
        prefix.append(f"--unit={unit}")
    stream = log.open("ab")
    process = subprocess.Popen([*prefix, "--", "env", "-i", *(f"{k}={v}" for k, v in env.items()), *command],
                               cwd=cwd, stdout=stream, stderr=stream, env=systemd_env())
    if wait:
        process.wait()
    return process


def build_bundle(walk_root: Path, env: dict[str, str]) -> float:
    """The browser-mode bundle (vite.browser.config.mjs), rebuilt every start so it matches the tree."""

    started = time.monotonic()
    process = scoped(None, [str(TAURI / "node_modules" / ".bin" / "vite"), "build", "--config",
                            str(TAURI / "vite.browser.config.mjs")], env, wait=True,
                     log=walk_root / "analyst" / "bundle_build.log", cwd=TAURI)
    if process.returncode != 0 or not (TAURI / "dist-browser" / "index.html").exists():
        raise SystemExit("the browser-mode bundle did not build (see analyst/bundle_build.log); "
                         "run `npm ci --offline` in apps/learnloop-tauri first")
    return time.monotonic() - started


def wait_for(path: Path, process: subprocess.Popen, seconds: float, what: str) -> dict:
    deadline = time.monotonic() + seconds
    while not path.exists():
        if process.poll() is not None:
            raise SystemExit(f"{what} exited before it was ready (see the walk's analyst/ directory)")
        if time.monotonic() > deadline:
            raise SystemExit(f"{what} was not ready within {int(seconds)} s")
        time.sleep(0.3)
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix in (".ready", ".json") else {}


def prepare_persona(walk_root: Path, brief: Path | None, files: list[Path]) -> Path:
    persona = walk_root / "persona"
    for name in ("files", "observations", "channel"):
        (persona / name).mkdir(parents=True, exist_ok=True)
    (persona / "brief.md").write_text(brief.read_text(encoding="utf-8") if brief else PLACEHOLDER_BRIEF,
                                      encoding="utf-8")
    walk = persona / "walk"
    shutil.copyfile(HERE / "walk_client.py", walk)
    walk.chmod(0o755)
    for source in files:
        shutil.copyfile(source, persona / "files" / source.name)
    return persona


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("name")
    parser.add_argument("--from", dest="start_point", choices=("empty", "fresh", "established"), required=True)
    parser.add_argument("--walks-dir", default=str(DEFAULT_WALKS))
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--files", type=Path, nargs="*",
                        help="this person's files (default: every sample document under samples/)")
    parser.add_argument("--phone", action="store_true", help="the phone app (learnloop_mobile) at a phone viewport")
    parser.add_argument("--anchor", help="the walk's date for the vault (default today, UTC)")
    parser.add_argument("--no-build", action="store_true", help="reuse apps/learnloop-tauri/dist-browser")
    parser.add_argument("--models", choices=("fake", "live"), default="fake",
                        help="live: the owner's ChatGPT-plan route (needs --allow-live-route and --config-dir)")
    parser.add_argument("--allow-live-route", action="store_true")
    parser.add_argument("--config-dir", type=Path, help="with --models live: the signed-in walk config directory")
    parser.add_argument("--decider", choices=("perplexity",),
                        help="with --models live: route the Decider tasks to the owner's Perplexity profile "
                             "(its key is read from the config directory's settings.env, as the app does)")
    args = parser.parse_args(argv)
    if args.models == "live" and (args.phone or not (args.allow_live_route and args.config_dir)):
        parser.error("--models live is desktop only and needs --allow-live-route and --config-dir")
    if args.decider and args.models != "live":
        parser.error("--decider goes with --models live (a faked walk has no Decider)")
    if args.phone and (refusal := phone_app_refusal()):
        raise SystemExit(refusal)

    walk_root = Path(args.walks_dir).resolve() / args.name
    if walk_root.exists():
        raise SystemExit(f"{walk_root} exists; a walk directory is never reused (stop.py, then pick a new name)")
    (walk_root / "analyst").mkdir(parents=True)
    env = clean_env(walk_root)
    python = str(ROOT / ".venv" / "bin" / "python")
    timings: dict[str, float] = {}
    if args.phone and args.start_point == "empty":
        raise SystemExit("the phone pairs with an existing library: use --from fresh or established")
    files = args.files if args.files is not None else default_files()
    persona = prepare_persona(walk_root, args.brief, files)

    vault = walk_root / "vault"
    if args.start_point != "empty":
        started = time.monotonic()
        command = [python, str(HERE / "make_vault.py"), args.start_point, str(vault)]
        if args.anchor:
            command += ["--anchor", args.anchor]
        process = scoped(None, command, env, wait=True, log=walk_root / "analyst" / "make_vault.log")
        if process.returncode != 0:
            raise SystemExit("the walk vault was not built (see analyst/make_vault.log)")
        timings["make_vault_s"] = round(time.monotonic() - started, 1)
        # make_vault's own bridge leaves its run files; the walk's bridge starts clean.
        for leftover in ("bridge.ready",):
            (walk_root / "run" / leftover).unlink(missing_ok=True)
    port = free_port()
    if args.phone:
        bridge_command = [python, str(HERE / "phone_proxy.py"), "--walk-root", str(walk_root), "--vault",
                          str(vault), "--port", str(port)]
    else:
        if not args.no_build:
            timings["bundle_build_s"] = round(build_bundle(walk_root, env), 1)
        bridge_command = [python, str(HERE / "bridge.py"), "--walk-root", str(walk_root), "--vault", str(vault),
                          "--port", str(port)]
        if args.start_point == "empty":
            bridge_command.append("--create-if-missing")
        if args.models == "live":
            bridge_command += ["--models", "live", "--allow-live-route", "--config-dir", str(args.config_dir)]
            if args.decider:
                bridge_command += ["--decider", args.decider]
    bridge_unit = f"uxwalk-{args.name}-bridge"
    bridge = scoped(bridge_unit, bridge_command, env, wait=False, log=walk_root / "analyst" / "bridge.out")
    ready = wait_for(walk_root / "run" / "bridge.ready", bridge, 240, "the bridge")
    url = f"http://127.0.0.1:{port}" + ready.get("start_path", "/")
    driver_unit = f"uxwalk-{args.name}-driver"
    driver_command = [python, str(HERE / "driver.py"), "--walk-root", str(walk_root), "--url", url,
                      "--bridge", f"http://127.0.0.1:{port}", "--viewport", "phone" if args.phone else "desktop"]
    driver = scoped(driver_unit, driver_command, env, wait=False, log=walk_root / "analyst" / "driver.out")
    wait_for(walk_root / "run" / "driver.ready", driver, 120, "the walk driver")
    wait_for(persona / "observations" / "0000.txt", driver, 120, "the first observation")
    record = {"name": args.name, "start_point": args.start_point, "phone": args.phone, "models": args.models,
              "decider": args.decider, "port": port,
              "units": [bridge_unit, driver_unit], "persona": str(persona), "vault": str(vault),
              "started_at": time.time(), "timings": timings}
    (walk_root / "run" / "walk.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))
    print(f"\nThe persona works in {persona} (only that directory): ./walk look")
    print(f"Stop it with: python scripts/ux_walk/stop.py {args.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
