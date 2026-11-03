#!/usr/bin/env python3
"""Build the sketch engine (Reader RW5d P2): QuickJS-ng compiled to WebAssembly.

Reproducible from pinned inputs, recorded in ``engine.lock.json``:

* ``quickjs-amalgam.zip``: QuickJS-ng's own amalgamated source release (MIT);
* ``wasi-sysroot``: wasi-libc headers and static libraries from the wasi-sdk
  release (MIT / Apache-2.0 WITH LLVM-exception / musl's MIT);
* ``libclang_rt``: compiler-rt builtins for wasm32 from the same release
  (Apache-2.0 WITH LLVM-exception).

Each download is checked against the SHA-256 the upstream release publishes
(recorded in the lock file); a mismatch stops the build. Nothing unpinned is
fetched, and nothing but sources and static libraries is used: the compiler
is the system ``clang`` (its major version is pinned too, because it decides
the output bytes) with ``wasm-ld``.

The output, ``apps/learnloop-tauri/src/screens/reader/figures/sketch/
sketch-engine.wasm``, must hash to ``output.sha256``. ``--check`` builds into
a temporary file and compares (the reproducibility check); ``--update-pin``
rewrites the pin after an intended change (then update
``learnloop.figures.sketch_engine.ENGINE_SHA256`` and ``sketchEngine.ts``'s
``ENGINE_SHA256`` to match; a test keeps the three equal).

**Variants** (``variants`` in the lock file): the same harness and the same pinned
sources under extra ``defines``, each with its own output and pin. RW5c's
``book-math-engine.wasm`` is the one: KaTeX's lexer needs the RegExp intrinsic, which a
sketch never gets, and a block through the page's markdown (``markdown/build.mjs``) needs more
work than a sketch's frame, so the sketch engine's bytes and caps are untouched (``--check``
proves it, rebuilding both).
The sidecar alone runs it (``learnloop.figures.katex_tree``; pin in ``KATEX_ENGINE_SHA256``).

Usage::

    python apps/learnloop-tauri/sketch-engine/build.py            # build, refuse a digest change
    python apps/learnloop-tauri/sketch-engine/build.py --check    # rebuild and compare only
    python apps/learnloop-tauri/sketch-engine/build.py --update-pin

Downloads are cached under ``$XDG_CACHE_HOME/learnloop-build/sketch-engine``
(``--cache`` to change); the repository holds only this script, the harness
(``sketch_engine.c``), the lock file, the licence notice and the artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parent
LOCK = HERE / "engine.lock.json"
HARNESS = HERE / "sketch_engine.c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(source: dict, cache: Path) -> Path:
    target = cache / "downloads" / source["file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(f"fetching {source['url']}", file=sys.stderr)
        partial = target.with_suffix(target.suffix + ".part")
        with urllib.request.urlopen(source["url"], timeout=300) as response, open(partial, "wb") as out:
            shutil.copyfileobj(response, out)
        partial.replace(target)
    got = sha256(target)
    if got != source["sha256"]:
        raise SystemExit(f"{source['file']}: sha256 {got} is not the pinned {source['sha256']}; refusing to build")
    return target


def _safe_members(names: list[str]) -> None:
    for name in names:
        if name.startswith("/") or ".." in Path(name).parts:
            raise SystemExit(f"refusing an archive member outside its directory: {name}")


def extract(cache: Path, sources: dict[str, Path], work: Path) -> dict[str, Path]:
    with zipfile.ZipFile(sources["quickjs"]) as archive:
        _safe_members(archive.namelist())
        archive.extractall(work / "quickjs")
    with tarfile.open(sources["libclang_rt"]) as archive:
        members = [m for m in archive.getmembers() if "/wasm32-unknown-wasip1/" in m.name and m.isfile()]
        _safe_members([m.name for m in members])
        archive.extractall(work / "rt", members=members, filter="data")
    with tarfile.open(sources["sysroot"]) as archive:
        wanted = re.compile(r"^[^/]+/(include/wasm32-wasip1/|lib/wasm32-wasip1/(crt1-reactor\.o|libc\.a)$)")
        members = [m for m in archive.getmembers() if wanted.match(m.name)]
        _safe_members([m.name for m in members])
        archive.extractall(work / "sysroot", members=members, filter="data")
    sysroot = next((work / "sysroot").iterdir())
    builtins = next((work / "rt").rglob("libclang_rt.builtins.a"))
    return {"quickjs": work / "quickjs", "sysroot": sysroot, "builtins": builtins}


def clang_major(clang: str) -> int:
    text = subprocess.run([clang, "--version"], capture_output=True, text=True, check=True).stdout
    found = re.search(r"clang version (\d+)\.", text)
    if not found:
        raise SystemExit(f"cannot read {clang}'s version")
    return int(found.group(1))


def build(lock: dict, cache: Path, output: Path, *, clang: str, wasm_ld: str, defines: tuple[str, ...] = ()) -> None:
    flags = lock["flags"]
    major = clang_major(clang)
    if major != lock["toolchain"]["clang_major"]:
        raise SystemExit(f"{clang} is clang {major}; the pin was built with clang {lock['toolchain']['clang_major']} "
                         "(another major version gives other bytes). Use that version, or --update-pin knowingly.")
    sources = {key: fetch(source, cache) for key, source in lock["sources"].items()}
    with tempfile.TemporaryDirectory(prefix="sketch-engine-") as temp:
        work = Path(temp)
        paths = extract(cache, sources, work)
        build_dir = work / "build"
        build_dir.mkdir()
        shutil.copy(HARNESS, build_dir / "sketch_engine.c")
        for name in ("quickjs-amalgam.c", "quickjs.h"):
            shutil.copy(paths["quickjs"] / name, build_dir / name)
        obj = build_dir / "sketch_engine.o"
        subprocess.run([clang, "--target=wasm32-wasip1", f"--sysroot={paths['sysroot']}", *flags["cflags"], *defines,
                        f"-ffile-prefix-map={build_dir}=/build", f"-ffile-prefix-map={work}=/work",
                        "-c", str(build_dir / "sketch_engine.c"), "-o", str(obj)], check=True, cwd=build_dir)
        lib = paths["sysroot"] / "lib" / "wasm32-wasip1"
        built = build_dir / "sketch-engine.wasm"
        subprocess.run([wasm_ld, str(lib / "crt1-reactor.o"), str(obj), str(lib / "libc.a"), str(paths["builtins"]),
                        *flags["ldflags"], "-o", str(built)], check=True, cwd=build_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(built, output)
        output.chmod(0o644)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cache", type=Path, default=Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
                        / "learnloop-build" / "sketch-engine")
    parser.add_argument("--check", action="store_true", help="rebuild into a temporary file and compare with the pin")
    parser.add_argument("--update-pin", action="store_true", help="accept the new output digest")
    parser.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
    parser.add_argument("--wasm-ld", default=os.environ.get("WASM_LD", "wasm-ld"))
    args = parser.parse_args(argv)
    lock = json.loads(LOCK.read_text())
    # The sketch engine, then each variant: one pin and one output apiece.
    targets = [("", lock["output"], ()),
               *((name, variant["output"], tuple(variant["defines"])) for name, variant in lock.get("variants", {}).items())]
    failed = False
    for name, pin, defines in targets:
        target = APP / pin["path"]
        with tempfile.TemporaryDirectory(prefix="sketch-engine-out-") as temp:
            out = Path(temp) / target.name
            build(lock, args.cache, out, clang=args.clang, wasm_ld=args.wasm_ld, defines=defines)
            got = sha256(out)
            if args.check:
                same = got == pin["sha256"]
                print(f"{'reproduced' if same else 'DIFFERENT'} {name or 'sketch-engine'}: {got}")
                failed = failed or not same
                continue
            if got != pin["sha256"] and not args.update_pin:
                print(f"{name or 'sketch-engine'}: the build gave {got}, not the pinned {pin['sha256']}; "
                      "nothing written (--update-pin to accept)", file=sys.stderr)
                failed = True
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out, target)
            target.chmod(0o644)
        if args.update_pin:
            pin["sha256"] = got
            pin["bytes"] = target.stat().st_size
        print(f"{target.relative_to(APP)}: {got}")
    if args.update_pin:
        LOCK.write_text(json.dumps(lock, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
