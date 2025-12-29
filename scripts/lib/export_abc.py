#!/usr/bin/env python3
"""Export TEF file to ABC notation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader


# MIDI pitch to ABC note mapping
def midi_to_abc(pitch: int) -> str:
    """Convert MIDI pitch to ABC notation.

    ABC convention:
    - C D E F G A B = C4 to B4 (MIDI 60-71)
    - c d e f g a b = C5 to B5 (MIDI 72-83)
    - C, D, E, = C3 to B3 (MIDI 48-59)
    - c' d' e' = C6+ (MIDI 84+)

    Uses flats for black keys to match common ABC style.
    """
    # Use flats instead of sharps for better readability
    notes = ['C', '_D', 'D', '_E', 'E', 'F', '_G', 'G', '_A', 'A', '_B', 'B']

    note_idx = pitch % 12
    note = notes[note_idx]
    octave = pitch // 12  # MIDI octave (60-71 = octave 5)

    # ABC middle octave is C4-B4 (MIDI 60-71)
    if 60 <= pitch <= 71:  # C4-B4
        return note
    elif 72 <= pitch <= 83:  # C5-B5
        return note.lower().replace('_', '_')  # lowercase, keep accidentals
    elif 48 <= pitch <= 59:  # C3-B3
        return note + ","
    elif 36 <= pitch <= 47:  # C2-B2
        return note + ",,"
    elif 84 <= pitch <= 95:  # C6-B6
        base = note.lower().replace('_', '_')
        return base + "'"
    else:
        # Fallback for extreme pitches
        if pitch >= 96:
            base = note.lower()
            return base + "'" * ((pitch - 72) // 12)
        else:
            return note + "," * ((59 - pitch) // 12 + 1)


def tef_to_abc(tef, output_path: Path):
    """Convert parsed TEF to ABC notation file."""

    # Get melody notes
    melody_notes = sorted(
        [e for e in tef.note_events if e.is_melody and e.decode_string_fret()],
        key=lambda e: e.position
    )

    if not melody_notes:
        print("No melody notes found!")
        return

    # ABC header
    lines = [
        f"X:1",
        f"T:{tef.title or 'Untitled'}",
        f"M:4/4",
        f"L:1/8",
        f"Q:1/4=160",
        f"K:G",
        f"%%MIDI program 105",  # Banjo
        f"",
    ]

    # Convert notes to ABC
    # Group by position to handle chords
    notes_by_pos = {}
    for evt in melody_notes:
        pitch = evt.get_pitch()
        if pitch:
            notes_by_pos.setdefault(evt.position, []).append(pitch)

    # Build ABC note string
    abc_notes = []
    positions = sorted(notes_by_pos.keys())

    # Calculate note durations based on gaps between positions
    for i, pos in enumerate(positions):
        pitches = notes_by_pos[pos]

        # Convert pitches to ABC
        if len(pitches) == 1:
            note_str = midi_to_abc(pitches[0])
        else:
            # Chord: [CEG]
            note_str = "[" + "".join(midi_to_abc(p) for p in sorted(pitches)) + "]"

        abc_notes.append(note_str)

        # Add bar lines roughly every 8 notes (assuming 8th notes in 4/4)
        if (i + 1) % 8 == 0:
            abc_notes.append("|")

        # Line break every 4 bars
        if (i + 1) % 32 == 0:
            abc_notes.append("\n")

    # Join notes with spaces
    abc_body = " ".join(abc_notes)
    lines.append(abc_body)
    lines.append("|]")  # End bar

    # Write file
    output_path.write_text("\n".join(lines))
    print(f"Wrote {len(melody_notes)} notes to {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: export_abc.py <file.tef> [output.abc]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Output path defaults to input name with .parsed.abc extension
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.parsed.abc')

    reader = TEFReader(input_path)
    tef = reader.parse()

    melody_notes = [e for e in tef.note_events if e.is_melody and e.decode_string_fret()]
    print(f"Parsing: {input_path.name}")
    print(f"Title: {tef.title}")
    print(f"Melody notes: {len(melody_notes)}")
    print()

    tef_to_abc(tef, output_path)


if __name__ == "__main__":
    main()
