#!/usr/bin/env python3
"""Compare parsed MIDI against expected MIDI with detailed output."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mido import MidiFile


def get_notes_with_timing(mid: MidiFile, track_idx: int = None):
    """Extract notes with absolute timing from MIDI file.

    Args:
        mid: MidiFile object
        track_idx: Specific track index, or None for all tracks

    Returns:
        List of (abs_time, pitch) tuples
    """
    notes = []
    tracks = [mid.tracks[track_idx]] if track_idx is not None else mid.tracks

    for track in tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append((abs_time, msg.note))

    return sorted(notes)


def compare_midi(expected_path: Path, actual_path: Path, expected_track: int = None):
    """Compare two MIDI files and print detailed analysis."""
    expected = MidiFile(str(expected_path))
    actual = MidiFile(str(actual_path))

    exp_notes = get_notes_with_timing(expected, expected_track)
    act_notes = get_notes_with_timing(actual)

    print(f"Expected: {len(exp_notes)} notes")
    print(f"Actual:   {len(act_notes)} notes")
    print()

    # Count pitch matches
    exp_pitches = [n[1] for n in exp_notes]
    act_pitches = [n[1] for n in act_notes]
    matches = sum(1 for a, b in zip(exp_pitches, act_pitches) if a == b)
    total = min(len(exp_pitches), len(act_pitches))

    print(f"Pitch matches: {matches}/{total} ({100*matches/total:.1f}%)")
    print()

    # Show first divergence
    print("Note-by-note comparison (first 30):")
    print(f"{'#':>4} {'Exp Time':>10} {'Exp Pitch':>10} {'Act Time':>10} {'Act Pitch':>10} {'Match':>6}")
    print("-" * 56)

    for i in range(min(30, len(exp_notes), len(act_notes))):
        et, ep = exp_notes[i]
        at, ap = act_notes[i]
        match = "OK" if ep == ap else "DIFF"
        time_diff = "" if abs(et - at) < 20 else f" (dt={at-et:+d})"
        print(f"{i:4d} {et:10d} {ep:10d} {at:10d} {ap:10d} {match:>6}{time_diff}")


def main():
    if len(sys.argv) < 3:
        print("Usage: compare.py <expected.mid> <actual.mid> [track_idx]")
        print()
        print("  expected.mid  - TablEdit's MIDI export (truth)")
        print("  actual.mid    - Parser's MIDI output")
        print("  track_idx     - Optional: specific track from expected (0-indexed)")
        sys.exit(1)

    expected = Path(sys.argv[1])
    actual = Path(sys.argv[2])
    track_idx = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not expected.exists():
        print(f"Error: {expected} not found")
        sys.exit(1)

    if not actual.exists():
        print(f"Error: {actual} not found")
        sys.exit(1)

    compare_midi(expected, actual, track_idx)


if __name__ == "__main__":
    main()
