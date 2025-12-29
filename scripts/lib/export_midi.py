#!/usr/bin/env python3
"""Export TEF file to MIDI for audio verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader
import mido


def tef_to_midi(tef, output_path: Path):
    """Convert parsed TEF to MIDI file.

    Uses estimated pitch (43 + pitch_byte) which is approximate.
    This lets us hear what we've parsed and compare to original.
    """
    mid = mido.MidiFile(ticks_per_beat=240)

    # Create a track for metadata
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage('track_name', name=tef.title or 'TEF Export'))
    meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(160)))

    # Create a track for note events
    note_track = mido.MidiTrack()
    mid.tracks.append(note_track)
    note_track.append(mido.MetaMessage('track_name', name='Parsed Notes'))

    # Get non-special note events, sorted by position
    note_events = sorted(
        [e for e in tef.note_events if e.marker in ('I', 'F', 'L')],
        key=lambda e: e.position
    )

    if not note_events:
        print("No note events found!")
        return

    # Convert TEF position to MIDI ticks (scale factor ~40)
    # TEF uses ~6 ticks per beat, MIDI uses 240 ticks per beat
    SCALE = 40

    # Build note on/off events
    midi_events = []
    for evt in note_events:
        tick = evt.position * SCALE
        pitch = evt.estimated_midi_pitch

        # Clamp pitch to valid MIDI range
        pitch = max(0, min(127, pitch))

        # Note on
        midi_events.append((tick, 'on', pitch, 80))
        # Note off after ~half beat (120 ticks)
        midi_events.append((tick + 120, 'off', pitch, 0))

    # Sort by time
    midi_events.sort(key=lambda x: (x[0], x[1] == 'on'))

    # Convert to delta times and add to track
    last_tick = 0
    for tick, event_type, pitch, velocity in midi_events:
        delta = tick - last_tick
        if event_type == 'on':
            note_track.append(mido.Message('note_on', note=pitch, velocity=velocity, time=delta))
        else:
            note_track.append(mido.Message('note_off', note=pitch, velocity=0, time=delta))
        last_tick = tick

    # End of track
    note_track.append(mido.MetaMessage('end_of_track', time=0))
    meta_track.append(mido.MetaMessage('end_of_track', time=0))

    mid.save(output_path)
    print(f"Wrote {len(note_events)} notes to {output_path}")
    print(f"Duration: ~{midi_events[-1][0] / 240 / 4:.1f} measures at 160 BPM")


def main():
    if len(sys.argv) < 2:
        print("Usage: export_midi.py <file.tef> [output.mid]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Output path defaults to input name with .parsed.mid extension
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.parsed.mid')

    reader = TEFReader(input_path)
    tef = reader.parse()

    print(f"Parsing: {input_path.name}")
    print(f"Title: {tef.title}")
    print(f"Note events: {len([e for e in tef.note_events if e.marker in ('I', 'F', 'L')])}")
    print()

    tef_to_midi(tef, output_path)
    print()
    print(f"Compare with original: {input_path.with_suffix('.mid')}")


if __name__ == "__main__":
    main()
