#!/usr/bin/env python3
"""Export TEF file to MIDI for audio verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tef_parser import TEFReader
import mido


def get_measure_for_position(position: int, ticks_per_measure: int) -> int:
    """Get 1-indexed measure number for a given TEF position."""
    return (position // ticks_per_measure) + 1


def expand_notes_with_reading_list(note_events, reading_list, ticks_per_measure: int):
    """Expand notes according to reading list playback order.

    Args:
        note_events: List of note events sorted by position
        reading_list: List of TEFReadingListEntry objects
        ticks_per_measure: TEF ticks per measure

    Returns:
        List of (output_tick, note_event) tuples in playback order
    """
    if not reading_list:
        # No reading list - play notes as-is
        return [(evt.position, evt) for evt in note_events]

    expanded = []
    output_measure_offset = 0  # Cumulative measures played

    for entry in reading_list:
        # Get notes in this measure range (inclusive)
        start_tick = (entry.from_measure - 1) * ticks_per_measure
        end_tick = entry.to_measure * ticks_per_measure  # Exclusive

        for evt in note_events:
            if start_tick <= evt.position < end_tick:
                # Calculate position relative to start of this range
                relative_pos = evt.position - start_tick
                # Add to output with offset for cumulative playback
                output_tick = output_measure_offset * ticks_per_measure + relative_pos
                expanded.append((output_tick, evt))

        # Advance the output offset
        measures_in_entry = entry.to_measure - entry.from_measure + 1
        output_measure_offset += measures_in_entry

    # Sort by output position
    expanded.sort(key=lambda x: x[0])
    return expanded


def tef_to_midi(tef, output_path: Path, melody_only: bool = True, track_filter: int = 0):
    """Convert parsed TEF to MIDI file.

    Args:
        tef: Parsed TEF file
        output_path: Output MIDI file path
        melody_only: If True, only export melody notes
        track_filter: Track index to export (0=first instrument, -1=all)
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

    # Get instrument info for track name and MIDI program
    if tef.instruments and track_filter >= 0 and track_filter < len(tef.instruments):
        inst = tef.instruments[track_filter]
        track_name = inst.name
    else:
        inst = None
        track_name = 'All Notes' if track_filter < 0 else 'Melody'
    note_track.append(mido.MetaMessage('track_name', name=track_name))

    # Set MIDI program based on instrument type
    # GM programs: 24=guitar, 25=acoustic guitar, 32=acoustic bass, 105=banjo, 22=harmonica, 105=banjo
    midi_program = 25  # Default to acoustic guitar
    if inst:
        name_lower = inst.name.lower()
        if 'banjo' in name_lower:
            midi_program = 105
        elif 'bass' in name_lower:
            midi_program = 32
        elif 'mandolin' in name_lower:
            midi_program = 25  # No mandolin in GM, use guitar
        elif 'guitar' in name_lower:
            midi_program = 25
        elif 'ukulele' in name_lower or 'uke' in name_lower:
            midi_program = 24
    note_track.append(mido.Message('program_change', program=midi_program, time=0))

    # Get note events, sorted by position
    # TuxGuitar format: track index in e.track, string in e.extra, fret in e.pitch_byte
    if melody_only:
        # Filter by track index (0=banjo, 1=guitar, etc.)
        note_events = sorted(
            [e for e in tef.note_events
             if e.is_melody
             and e.decode_string_fret()
             and (track_filter < 0 or e.track == track_filter)],
            key=lambda e: e.position
        )
    else:
        note_events = sorted(
            [e for e in tef.note_events
             if track_filter < 0 or e.track == track_filter],
            key=lambda e: e.position
        )

    if not note_events:
        print("No note events found!")
        return

    # Get tuning from file (default to Open G if not found)
    tuning = [62, 59, 55, 50, 67]  # Default Open G banjo
    if tef.instruments and track_filter >= 0 and track_filter < len(tef.instruments):
        inst = tef.instruments[track_filter]
        if inst.tuning_pitches:
            tuning = inst.tuning_pitches

    # Filter out hammer-on decoration notes (L marker, b6=0)
    # These are articulation decorations that shouldn't be separate MIDI notes.
    # Pattern 1: +1 semitone to next note (chromatic approach)
    # Pattern 2: +1 semitone from previous note (hammer-on within a roll)
    filtered_events = []
    for i, evt in enumerate(note_events):
        if evt.marker == 'L' and evt.raw_data and evt.raw_data[6] == 0:
            s, f = evt.decode_string_fret()
            this_pitch = tuning[s - 1] + f

            # Check if next note is +1 semitone (chromatic hammer-on target)
            if i + 1 < len(note_events):
                next_evt = note_events[i + 1]
                ns, nf = next_evt.decode_string_fret() if next_evt.decode_string_fret() else (0, 0)
                next_pitch = tuning[ns - 1] + nf if ns > 0 else 0
                if next_pitch - this_pitch == 1:
                    continue  # Skip chromatic approach note

            # Check if prev note is -1 semitone AND prev is also an L note
            # This catches the second note in a hammer-on pair (57→58) regardless of next
            if i > 0:
                prev_evt = note_events[i - 1]
                if prev_evt.marker == 'L':  # Both in a hammer-on sequence
                    ps, pf = prev_evt.decode_string_fret() if prev_evt.decode_string_fret() else (0, 0)
                    prev_pitch = tuning[ps - 1] + pf if ps > 0 else 0
                    if this_pitch - prev_pitch == 1:
                        # Check that next note is higher (ascending run continuation)
                        if i + 1 < len(note_events):
                            next_evt = note_events[i + 1]
                            ns, nf = next_evt.decode_string_fret() if next_evt.decode_string_fret() else (0, 0)
                            next_pitch = tuning[ns - 1] + nf if ns > 0 else 0
                            if next_pitch > this_pitch:
                                continue  # Skip decoration in ascending run

        filtered_events.append(evt)
    note_events = filtered_events

    # TuxGuitar format: position is in 16th note grid
    # 16 positions per measure in 4/4, 4 positions per beat
    # MIDI: 240 ticks/beat, so 60 MIDI ticks per position
    TICKS_PER_POSITION = 60  # 240 ticks/beat / 4 positions/beat
    POSITIONS_PER_MEASURE = 16  # 4/4 time signature

    # Expand notes using reading list if available
    expanded_notes = expand_notes_with_reading_list(
        note_events, tef.reading_list, POSITIONS_PER_MEASURE
    )

    print(f"Source notes: {len(note_events)}, Expanded: {len(expanded_notes)}")
    if tef.reading_list:
        print(f"Reading list: {len(tef.reading_list)} entries")

    # Build note on/off events
    # Use gap to next note as duration (or default if last note)
    midi_events = []
    for i, (output_pos, evt) in enumerate(expanded_notes):
        # Convert position (16th notes) to MIDI ticks
        tick = output_pos * TICKS_PER_POSITION

        # Use decoded pitch with file's tuning
        pitch = evt.get_pitch(tuning)
        if pitch is None:
            continue

        # Clamp pitch to valid MIDI range
        pitch = max(0, min(127, pitch))

        # Calculate duration from gap to next note
        if i + 1 < len(expanded_notes):
            next_pos = expanded_notes[i + 1][0]
            gap_ticks = (next_pos - output_pos) * TICKS_PER_POSITION
            duration = max(gap_ticks - 10, 60)  # Leave small gap, minimum 60 ticks
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
    print(f"Wrote {len(expanded_notes)} notes to {output_path}")
    print(f"Duration: ~{midi_events[-1][0] / 240 / 4:.1f} measures at 160 BPM")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Export TEF file to MIDI')
    parser.add_argument('input', help='Input TEF file')
    parser.add_argument('output', nargs='?', help='Output MIDI file (default: input.parsed.mid)')
    parser.add_argument('-t', '--track', type=int, default=0,
                        help='Track index to export (default: 0, use -1 for all)')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List tracks and exit')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    reader = TEFReader(input_path)
    tef = reader.parse()

    # Show file info
    print(f"File: {input_path.name}")
    print(f"Title: {tef.title}")
    print(f"Version: {tef.header.version}")

    # Show tracks
    print(f"\nTracks ({len(tef.instruments)}):")
    from collections import Counter
    track_counts = Counter(e.track for e in tef.note_events if e.is_melody)
    for i, inst in enumerate(tef.instruments):
        note_count = track_counts.get(i, 0)
        print(f"  {i}: {inst.name} ({inst.num_strings} strings) - {note_count} notes")

    if args.list:
        sys.exit(0)

    # Output path defaults to input name with .parsed.mid extension
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.parsed.mid')

    print()
    tef_to_midi(tef, output_path, melody_only=True, track_filter=args.track)
    print()
    print(f"Compare with original: {input_path.with_suffix('.mid')}")


if __name__ == "__main__":
    main()
