#!/usr/bin/env python3
"""CLI for TEF file parser."""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .reader import TEFReader


def cmd_parse(args):
    """Parse TEF file and dump structure."""
    path = Path(args.input)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    reader = TEFReader(path)
    tef = reader.parse()
    print(tef.dump())

    if args.verbose:
        print("\n\nAll strings found:")
        for s in tef.strings:
            print(f"  0x{s.offset:04x}: [{s.length:2d}] {s.value!r}")

    return 0


def cmd_version(args):
    """Show TEF file version."""
    path = Path(args.input)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    with open(path, 'rb') as f:
        h = f.read(4)
    print(f"TEF version: {h[3]}.{h[2]:02d}")
    return 0


def cmd_view(args):
    """View parsed tablature as ASCII timeline."""
    path = Path(args.input)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    reader = TEFReader(path)
    tef = reader.parse()

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
        return 0

    positions = sorted(events_by_pos.keys())
    max_pos = max(positions)

    print(f"Note Events: {sum(len(v) for v in events_by_pos.values())} events")
    print(f"Positions: {len(positions)} unique ({min(positions)} to {max_pos})")
    print()

    # Articulation and marker symbols
    ART_SYMBOLS = {0: ' ', 1: 'H', 2: 'P', 3: 'S'}
    MARKER_SYMBOLS = {'I': '*', 'F': 'o', 'L': '~', 'S': '#'}

    print("=" * 80)
    print("TIMELINE VIEW (tick positions)")
    print("=" * 80)
    print()

    # Group by sections
    SECTION_SIZE = 50
    sections = defaultdict(list)
    for pos in positions:
        section = pos // SECTION_SIZE
        sections[section].append(pos)

    for section in sorted(sections.keys())[:20]:
        start = section * SECTION_SIZE
        end = start + SECTION_SIZE
        print(f"--- Ticks {start:3d} to {end:3d} ---")

        for pos in sorted(sections[section]):
            events = events_by_pos[pos]
            event_strs = []
            for e in events:
                art = ART_SYMBOLS.get(e.extra, '?')
                marker = MARKER_SYMBOLS.get(e.marker, '?')
                event_strs.append(f"T{e.track}{marker}{art}(b9={e.pitch_byte:2d},b11={e.b11:3d})")
            events_str = ' '.join(event_strs)
            print(f"  {pos:4d}: {events_str}")
        print()

    # Summary sections
    print("=" * 80)
    print("TRACK DISTRIBUTION")
    print("=" * 80)
    track_counts = defaultdict(int)
    for events in events_by_pos.values():
        for e in events:
            track_counts[e.track] += 1
    for track, count in sorted(track_counts.items()):
        print(f"  Track {track}: {count:4d} events")

    return 0


def expand_notes_with_reading_list(note_events, reading_list, ticks_per_measure: int):
    """Expand notes according to reading list playback order."""
    if not reading_list:
        return [(evt.position, evt) for evt in note_events]

    expanded = []
    output_measure_offset = 0

    for entry in reading_list:
        start_tick = (entry.from_measure - 1) * ticks_per_measure
        end_tick = entry.to_measure * ticks_per_measure

        for evt in note_events:
            if start_tick <= evt.position < end_tick:
                relative_pos = evt.position - start_tick
                output_tick = output_measure_offset * ticks_per_measure + relative_pos
                expanded.append((output_tick, evt))

        measures_in_entry = entry.to_measure - entry.from_measure + 1
        output_measure_offset += measures_in_entry

    expanded.sort(key=lambda x: x[0])
    return expanded


def cmd_midi(args):
    """Export TEF file to MIDI."""
    try:
        import mido
    except ImportError:
        print("Error: mido package required. Install with: uv add mido", file=sys.stderr)
        return 1

    path = Path(args.input)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    reader = TEFReader(path)
    tef = reader.parse()

    print(f"File: {path.name}")
    print(f"Title: {tef.title}")
    print(f"Version: {tef.header.version}")

    # Show tracks
    print(f"\nTracks ({len(tef.instruments)}):")
    track_counts = Counter(e.track for e in tef.note_events if e.is_melody)
    for i, inst in enumerate(tef.instruments):
        note_count = track_counts.get(i, 0)
        print(f"  {i}: {inst.name} ({inst.num_strings} strings) - {note_count} notes")

    if args.list:
        return 0

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = path.with_suffix('.parsed.mid')

    track_filter = args.track

    # Create MIDI file
    mid = mido.MidiFile(ticks_per_beat=240)

    # Metadata track
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage('track_name', name=tef.title or 'TEF Export'))
    meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(160)))

    # Note track
    note_track = mido.MidiTrack()
    mid.tracks.append(note_track)

    # Get instrument info
    if tef.instruments and 0 <= track_filter < len(tef.instruments):
        inst = tef.instruments[track_filter]
        track_name = inst.name
    else:
        inst = None
        track_name = 'All Notes' if track_filter < 0 else 'Melody'
    note_track.append(mido.MetaMessage('track_name', name=track_name))

    # Set MIDI program
    midi_program = 25  # acoustic guitar
    if inst:
        name_lower = inst.name.lower()
        if 'banjo' in name_lower:
            midi_program = 105
        elif 'bass' in name_lower:
            midi_program = 32
        elif 'mandolin' in name_lower:
            midi_program = 25
    note_track.append(mido.Message('program_change', program=midi_program, time=0))

    # Get melody notes for selected track
    note_events = sorted(
        [e for e in tef.note_events
         if e.is_melody and e.decode_string_fret()
         and (track_filter < 0 or e.track == track_filter)],
        key=lambda e: e.position
    )

    if not note_events:
        print("No note events found!")
        return 1

    # Get tuning
    tuning = [62, 59, 55, 50, 67]  # Default Open G banjo
    if tef.instruments and 0 <= track_filter < len(tef.instruments):
        inst = tef.instruments[track_filter]
        if inst.tuning_pitches:
            tuning = inst.tuning_pitches

    # Filter hammer-on decorations
    filtered_events = []
    for i, evt in enumerate(note_events):
        if evt.marker == 'L' and evt.raw_data and evt.raw_data[6] == 0:
            s, f = evt.decode_string_fret()
            this_pitch = tuning[s - 1] + f
            if i + 1 < len(note_events):
                next_evt = note_events[i + 1]
                ns, nf = next_evt.decode_string_fret() if next_evt.decode_string_fret() else (0, 0)
                next_pitch = tuning[ns - 1] + nf if ns > 0 else 0
                if next_pitch - this_pitch == 1:
                    continue
            if i > 0:
                prev_evt = note_events[i - 1]
                if prev_evt.marker == 'L':
                    ps, pf = prev_evt.decode_string_fret() if prev_evt.decode_string_fret() else (0, 0)
                    prev_pitch = tuning[ps - 1] + pf if ps > 0 else 0
                    if this_pitch - prev_pitch == 1:
                        if i + 1 < len(note_events):
                            next_evt = note_events[i + 1]
                            ns, nf = next_evt.decode_string_fret() if next_evt.decode_string_fret() else (0, 0)
                            next_pitch = tuning[ns - 1] + nf if ns > 0 else 0
                            if next_pitch > this_pitch:
                                continue
        filtered_events.append(evt)
    note_events = filtered_events

    # Timing constants
    TICKS_PER_POSITION = 60
    POSITIONS_PER_MEASURE = 16

    # Expand with reading list
    expanded_notes = expand_notes_with_reading_list(
        note_events, tef.reading_list, POSITIONS_PER_MEASURE
    )

    print(f"\nSource notes: {len(note_events)}, Expanded: {len(expanded_notes)}")
    if tef.reading_list:
        print(f"Reading list: {len(tef.reading_list)} entries")

    # Build MIDI events
    midi_events = []
    for i, (output_pos, evt) in enumerate(expanded_notes):
        tick = output_pos * TICKS_PER_POSITION
        pitch = evt.get_pitch(tuning)
        if pitch is None:
            continue
        pitch = max(0, min(127, pitch))

        if i + 1 < len(expanded_notes):
            next_pos = expanded_notes[i + 1][0]
            gap_ticks = (next_pos - output_pos) * TICKS_PER_POSITION
            duration = max(gap_ticks - 10, 60)
        else:
            duration = 240

        midi_events.append((tick, 'on', pitch, 80))
        midi_events.append((tick + duration, 'off', pitch, 0))

    midi_events.sort(key=lambda x: (x[0], x[1] == 'on'))

    # Convert to delta times
    last_tick = 0
    for tick, event_type, pitch, velocity in midi_events:
        delta = tick - last_tick
        if event_type == 'on':
            note_track.append(mido.Message('note_on', note=pitch, velocity=velocity, time=delta))
        else:
            note_track.append(mido.Message('note_off', note=pitch, velocity=0, time=delta))
        last_tick = tick

    note_track.append(mido.MetaMessage('end_of_track', time=0))
    meta_track.append(mido.MetaMessage('end_of_track', time=0))

    mid.save(output_path)
    print(f"Wrote {len(expanded_notes)} notes to {output_path}")
    print(f"Duration: ~{midi_events[-1][0] / 240 / 4:.1f} measures at 160 BPM")

    return 0


def cmd_otf(args):
    """Export TEF file to OTF (Open Tab Format)."""
    from .otf import tef_to_otf

    path = Path(args.input)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    reader = TEFReader(path)
    tef = reader.parse()

    # Convert to OTF
    otf_doc = tef_to_otf(tef)

    # Determine output format and path
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = ".otf.json" if args.json else ".otf.yaml"
        output_path = path.with_suffix(suffix)

    # Generate output
    if args.json or output_path.suffix == ".json":
        content = otf_doc.to_json(indent=2)
    else:
        content = otf_doc.to_yaml()

    # Write or print
    if args.stdout:
        print(content)
    else:
        output_path.write_text(content)
        print(f"Wrote {output_path}")
        print(f"  Tracks: {len(otf_doc.tracks)}")
        total_notes = sum(
            sum(len(e.notes) for m in measures for e in m.events)
            for measures in otf_doc.notation.values()
        )
        print(f"  Notes: {total_notes}")
        if otf_doc.reading_list:
            print(f"  Reading list: {len(otf_doc.reading_list)} entries")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='tef',
        description='TEF file parser for TablEdit tablature files',
    )
    parser.add_argument('--version', action='version', version='tef-parser 0.1.0')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # parse command
    p_parse = subparsers.add_parser('parse', help='Parse TEF file and dump structure')
    p_parse.add_argument('input', help='Input TEF file')
    p_parse.add_argument('-v', '--verbose', action='store_true', help='Show all strings')
    p_parse.set_defaults(func=cmd_parse)

    # version command
    p_version = subparsers.add_parser('version', help='Show TEF file version')
    p_version.add_argument('input', help='Input TEF file')
    p_version.set_defaults(func=cmd_version)

    # view command
    p_view = subparsers.add_parser('view', help='View parsed tablature as ASCII timeline')
    p_view.add_argument('input', help='Input TEF file')
    p_view.set_defaults(func=cmd_view)

    # midi command
    p_midi = subparsers.add_parser('midi', help='Export TEF file to MIDI')
    p_midi.add_argument('input', help='Input TEF file')
    p_midi.add_argument('output', nargs='?', help='Output MIDI file (default: input.parsed.mid)')
    p_midi.add_argument('-t', '--track', type=int, default=0,
                        help='Track index to export (default: 0, use -1 for all)')
    p_midi.add_argument('-l', '--list', action='store_true', help='List tracks and exit')
    p_midi.set_defaults(func=cmd_midi)

    # otf command
    p_otf = subparsers.add_parser('otf', help='Export TEF file to OTF (Open Tab Format)')
    p_otf.add_argument('input', help='Input TEF file')
    p_otf.add_argument('output', nargs='?', help='Output OTF file (default: input.otf.yaml)')
    p_otf.add_argument('--json', action='store_true', help='Output as JSON instead of YAML')
    p_otf.add_argument('--stdout', action='store_true', help='Print to stdout instead of file')
    p_otf.set_defaults(func=cmd_otf)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
