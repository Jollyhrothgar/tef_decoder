#!/usr/bin/env python3
"""Export TEF file to JSON format for archiving."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader


def tef_to_dict(tef) -> dict:
    """Convert TEFFile to a dictionary for JSON export."""
    return {
        "file": tef.path.name,
        "version": tef.header.version,
        "title": tef.title,
        "instruments": [
            {
                "name": inst.name,
                "strings": inst.num_strings,
                "tuning": inst.tuning_pitches,
            }
            for inst in tef.instruments
        ],
        "sections": [s.name for s in tef.sections],
        "chords": [c.name for c in tef.chords],
        "note_events": {
            "count": len(tef.note_events),
            "positions": len(set(e.position for e in tef.note_events)),
            "events": [
                {
                    "position": e.position,
                    "track": e.track,
                    "marker": e.marker,
                    "articulation": e.articulation,
                    "pitch_byte": e.pitch_byte,
                    "b11": e.b11,
                    "estimated_pitch": e.estimated_midi_pitch,
                }
                for e in tef.note_events
            ],
        },
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: export_json.py <file.tef> [--pretty]")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    pretty = "--pretty" in sys.argv

    reader = TEFReader(path)
    tef = reader.parse()
    data = tef_to_dict(tef)

    if pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))


if __name__ == "__main__":
    main()
