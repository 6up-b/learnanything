from __future__ import annotations

import sys

from learnloop_sidecar.logging import configure_logging
from learnloop_sidecar.server import serve


def main() -> None:
    configure_logging()
    serve(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()

