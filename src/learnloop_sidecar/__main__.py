from __future__ import annotations

import sys
from pathlib import Path

from learnloop.config import load_dotenv
from learnloop_sidecar.logging import configure_logging
from learnloop_sidecar.server import serve


def main() -> None:
    # Tauri launches the sidecar with the LearnAnything checkout as cwd. Keep
    # per-machine checkout paths and debug credentials in that ignored .env so
    # they apply to every vault opened by this desktop checkout.
    load_dotenv(Path.cwd() / ".env")
    configure_logging()
    serve(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
