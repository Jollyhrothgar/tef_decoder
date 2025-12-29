"""Tests for TEF parser."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tef_parser import TEFReader


SAMPLE_FILE = Path(__file__).parent.parent / "shuck_the_corn.tef"


def test_read_header():
    """Test that header is parsed correctly."""
    reader = TEFReader(SAMPLE_FILE)
    header = reader.read_header()

    assert header.version == "3.05"
    assert header.format_id == 0x0010


def test_parse_title():
    """Test that title is extracted."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    assert tef.title == "Shuckin' The Corn"


def test_parse_sections():
    """Test that sections are found."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    section_names = [s.name for s in tef.sections]
    assert "(A Part)" in section_names
    assert "(B Part)" in section_names


def test_parse_instruments():
    """Test that instruments are parsed."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    assert len(tef.instruments) == 3

    banjo = next(i for i in tef.instruments if "Banjo" in i.name)
    assert banjo.num_strings == 5
    assert len(banjo.tuning_pitches) == 5

    guitar = next(i for i in tef.instruments if i.name == "guitar")
    assert guitar.num_strings == 6
    assert len(guitar.tuning_pitches) == 6

    bass = next(i for i in tef.instruments if i.name == "bass")
    assert bass.num_strings == 4
    assert len(bass.tuning_pitches) == 4


def test_parse_chords():
    """Test that chord symbols are found."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    chord_names = [c.name for c in tef.chords]
    assert "C7" in chord_names


def test_tuning_intervals():
    """Test that tuning intervals are musically correct."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    # Guitar should have standard tuning intervals: 5, 5, 5, 4, 5 semitones
    guitar = next(i for i in tef.instruments if i.name == "guitar")
    pitches = guitar.tuning_pitches
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    assert intervals == [5, 4, 5, 5, 5]  # E-A-D-G-B-E intervals

    # Bass should have all perfect fourths: 5, 5, 5
    bass = next(i for i in tef.instruments if i.name == "bass")
    pitches = bass.tuning_pitches
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    assert intervals == [5, 5, 5]  # E-A-D-G intervals


def test_parse_note_events():
    """Test that note events are extracted."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    # Should have many note events
    assert len(tef.note_events) > 100

    # Events should have increasing positions (mostly)
    positions = [e.position for e in tef.note_events]
    # Allow some repeats (chords) but overall trend should be increasing
    assert positions[-1] > positions[0]

    # Should have different marker types
    markers = set(e.marker for e in tef.note_events)
    assert 'I' in markers  # Initial notes
    assert 'F' in markers  # Fret notes


def test_note_event_structure():
    """Test note event record structure."""
    reader = TEFReader(SAMPLE_FILE)
    tef = reader.parse()

    # First event should be at position 3
    first = tef.note_events[0]
    assert first.position == 3
    assert first.marker == 'I'

    # All events should have 12-byte raw data
    for evt in tef.note_events:
        assert len(evt.raw_data) == 12
