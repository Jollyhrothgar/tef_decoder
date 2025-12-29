#!/usr/bin/env python3
"""Export TEF file to MIDI for audio verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader
import mido


def tef_to_midi(tef, output_path: Path, melody_only: bool = True):
    """Convert parsed TEF to MIDI file.

    Args:
        tef: Parsed TEF file
        output_path: Output MIDI file path
        melody_only: If True, only export melody notes (b9 > 0)
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
    track_name = 'Banjo Melody' if melody_only else 'All Notes'
    note_track.append(mido.MetaMessage('track_name', name=track_name))
    # Set instrument to banjo (GM program 105)
    note_track.append(mido.Message('program_change', program=105, time=0))

    # Get note events, sorted by position
    if melody_only:
        # Only melody notes that we can decode
        note_events = sorted(
            [e for e in tef.note_events if e.is_melody and e.decode_string_fret()],
            key=lambda e: e.position
        )
    else:
        note_events = sorted(
            [e for e in tef.note_events if e.marker in ('I', 'F', 'L')],
            key=lambda e: e.position
        )

    if not note_events:
        print("No note events found!")
        return

    # Convert TEF position to MIDI ticks
    # Scale factor depends on position values:
    # - If positions are small (0-1000 range), scale up by ~0.375
    # - If positions are large (1000+ range), scale down by 0.125

    # Calculate scale based on position range
    max_pos = max(e.position for e in note_events) if note_events else 0
    min_nonzero = min((e.position for e in note_events if e.position > 0), default=320)

    if min_nonzero >= 900:
        # Large position values (like shuck_the_corn: 960, 1920, 3840...)
        # Scale down: TEF 960 -> MIDI 120 (eighth note)
        SCALE = 0.125
    else:
        # Small position values (like Multi Note: 0, 320, 640...)
        # Scale down slightly: TEF 320 -> MIDI 120 (eighth note)
        SCALE = 0.375

    # Build note on/off events
    # Use gap to next note as duration (or default if last note)
    midi_events = []
    for i, evt in enumerate(note_events):
        tick = int(evt.position * SCALE)

        # Use decoded pitch for melody, fallback for others
        pitch = evt.get_pitch()
        if pitch is None:
            continue

        # Clamp pitch to valid MIDI range
        pitch = max(0, min(127, pitch))

        # Calculate duration from gap to next note
        if i + 1 < len(note_events):
            gap = note_events[i + 1].position - evt.position
            duration = max(int(gap * SCALE) - 10, 60)  # Leave small gap, minimum 60 ticks
        else:
            duration = 240  # Default one beat for last note

        # Note on
        midi_events.append((tick, 'on', pitch, 80))
        # Note off based on calculated duration
        midi_events.append((tick + duration, 'off', pitch, 0))

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

    melody_notes = [e for e in tef.note_events if e.is_melody and e.decode_string_fret()]
    print(f"Parsing: {input_path.name}")
    print(f"Title: {tef.title}")
    print(f"Melody notes: {len(melody_notes)}")
    print()

    tef_to_midi(tef, output_path, melody_only=True)
    print()
    print(f"Compare with original: {input_path.with_suffix('.mid')}")


if __name__ == "__main__":
    main()
