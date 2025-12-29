#!/usr/bin/env python3
"""ASCII tablature viewer for parsed TEF files.

Displays parsed note events as ASCII tablature, showing:
- Timing positions
- Track/voice information
- Articulation markers (H=hammer-on, P=pull-off, S=slide)
- Raw encoding values for analysis
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader


def view_tablature(tef, measures_per_line=4, beats_per_measure=4):
    """Display parsed TEF as ASCII tablature."""

    print(f"Title: {tef.title}")
    print(f"Version: {tef.header.version}")
    print()

    if tef.instruments:
        print("Instruments:")
        for inst in tef.instruments:
            print(f"  {inst.name} ({inst.num_strings} strings)")
        print()

    # Get note events grouped by position
    events_by_pos = defaultdict(list)
    for e in tef.note_events:
        if e.marker in ('I', 'F', 'L'):
            events_by_pos[e.position].append(e)

    if not events_by_pos:
        print("No note events found.")
        return

    positions = sorted(events_by_pos.keys())
    max_pos = max(positions)

    print(f"Note Events: {sum(len(v) for v in events_by_pos.values())} events")
    print(f"Positions: {len(positions)} unique ({min(positions)} to {max_pos})")
    print()

    # Articulation symbols
    ART_SYMBOLS = {
        0: ' ',  # normal
        1: 'H',  # hammer-on
        2: 'P',  # pull-off
        3: 'S',  # slide
    }

    # Marker symbols
    MARKER_SYMBOLS = {
        'I': '●',  # Initial/attack
        'F': '○',  # Fret
        'L': '~',  # Legato
        'S': '□',  # Special
    }

    # Display as timeline
    print("=" * 80)
    print("TIMELINE VIEW (tick positions)")
    print("=" * 80)
    print()

    # Group by sections of 100 ticks
    SECTION_SIZE = 50
    sections = defaultdict(list)
    for pos in positions:
        section = pos // SECTION_SIZE
        sections[section].append(pos)

    for section in sorted(sections.keys())[:20]:  # First 20 sections
        start = section * SECTION_SIZE
        end = start + SECTION_SIZE
        print(f"--- Ticks {start:3d} to {end:3d} ---")

        for pos in sorted(sections[section]):
            events = events_by_pos[pos]

            # Build event summary
            event_strs = []
            for e in events:
                art = ART_SYMBOLS.get(e.extra, '?')
                marker = MARKER_SYMBOLS.get(e.marker, '?')
                # Show track, marker, articulation, and raw values
                event_strs.append(f"T{e.track}{marker}{art}(b9={e.pitch_byte:2d},b11={e.b11:3d})")

            events_str = ' '.join(event_strs)
            print(f"  {pos:4d}: {events_str}")
        print()

    # Show articulation summary
    print("=" * 80)
    print("ARTICULATION SUMMARY")
    print("=" * 80)
    art_counts = defaultdict(int)
    for pos, events in events_by_pos.items():
        for e in events:
            art_counts[e.articulation] += 1

    for art, count in sorted(art_counts.items()):
        print(f"  {art:12s}: {count:4d}")
    print()

    # Show track distribution
    print("=" * 80)
    print("TRACK/VOICE DISTRIBUTION")
    print("=" * 80)
    track_counts = defaultdict(int)
    for pos, events in events_by_pos.items():
        for e in events:
            track_counts[e.track] += 1

    for track, count in sorted(track_counts.items()):
        print(f"  Track {track}: {count:4d} events")
    print()

    # Show b9 value distribution
    print("=" * 80)
    print("B9 (PITCH_BYTE) DISTRIBUTION")
    print("=" * 80)
    b9_counts = defaultdict(int)
    for pos, events in events_by_pos.items():
        for e in events:
            b9_counts[e.pitch_byte] += 1

    for b9, count in sorted(b9_counts.items()):
        print(f"  b9={b9:2d}: {count:4d} events")
    print()

    # Show b11 value distribution
    print("=" * 80)
    print("B11 DISTRIBUTION (possible string/fret encoding)")
    print("=" * 80)
    b11_counts = defaultdict(int)
    for pos, events in events_by_pos.items():
        for e in events:
            b11_counts[e.b11] += 1

    for b11, count in sorted(b11_counts.items()):
        # Decode as potential string/fret
        hi3 = b11 >> 5
        lo = (b11 & 0x1f) >> 3
        print(f"  b11={b11:3d} (s{hi3+1} f{lo}): {count:4d} events")


def main():
    if len(sys.argv) < 2:
        print("Usage: view_tab.py <file.tef>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    reader = TEFReader(input_path)
    tef = reader.parse()

    view_tablature(tef)


if __name__ == "__main__":
    main()
