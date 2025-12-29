#!/usr/bin/env python3
"""TEF Parser - Parse TablEdit .tef files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tef_parser import TEFReader


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.tef>")
        sys.exit(1)

    path = Path(sys.argv[1])
    reader = TEFReader(path)
    tef = reader.parse()
    print(tef.dump())


if __name__ == "__main__":
    main()
