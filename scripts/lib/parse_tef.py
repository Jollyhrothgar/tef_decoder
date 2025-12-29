#!/usr/bin/env python3
"""Parse a TEF file and dump its structure."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_tef.py <file.tef>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    reader = TEFReader(path)
    tef = reader.parse()
    print(tef.dump())

    # Show raw strings for debugging
    if "--verbose" in sys.argv or "-v" in sys.argv:
        print("\n\nAll strings found:")
        for s in tef.strings:
            print(f"  0x{s.offset:04x}: [{s.length:2d}] {s.value!r}")


if __name__ == "__main__":
    main()
