"""``python -m learnloop_mcp --vault V``: the stdio server, for development clients."""

import argparse
from pathlib import Path

from learnloop_mcp.cli import serve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    serve(args.vault, transport="stdio")


if __name__ == "__main__":
    main()
