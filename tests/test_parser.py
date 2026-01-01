"""Tests for TEF parser."""

from pathlib import Path

from tef_parser import TEFReader


SAMPLE_FILE = Path(__file__).parent.parent / "samples" / "songs" / "shuck_the_corn.tef"
V2_SAMPLE_FILE = Path(__file__).parent.parent / "samples" / "songs" / "mandolin_foggy_mountain_breakdown.tef"


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

    # Guitar should have standard tuning intervals: 5, 4, 5, 5, 5 semitones
    # (from high to low: E-B-G-D-A-E)
    guitar = next(i for i in tef.instruments if i.name == "guitar")
    pitches = guitar.tuning_pitches
    # Intervals from string 1 to string 6 (high to low) are descending
    intervals = [abs(pitches[i+1] - pitches[i]) for i in range(len(pitches)-1)]
    assert intervals == [5, 4, 5, 5, 5]  # E-B-G-D-A-E intervals

    # Bass should have all perfect fourths: 5, 5, 5
    bass = next(i for i in tef.instruments if i.name == "bass")
    pitches = bass.tuning_pitches
    intervals = [abs(pitches[i+1] - pitches[i]) for i in range(len(pitches)-1)]
    assert intervals == [5, 5, 5]  # G-D-A-E intervals


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

    # First event should be near the start (position may vary slightly)
    first = tef.note_events[0]
    assert first.position < 10  # First note is early in the piece
    assert first.marker == 'I'

    # All events should have 12-byte raw data (v3 format)
    for evt in tef.note_events:
        assert len(evt.raw_data) == 12


def test_v2_file_parsing():
    """Test that v2 format files are parsed correctly."""
    if not V2_SAMPLE_FILE.exists():
        import pytest
        pytest.skip("V2 sample file not found")

    reader = TEFReader(V2_SAMPLE_FILE)
    tef = reader.parse()

    # Check v2-specific header fields
    assert tef.header.is_v2
    assert tef.header.version == "2.00"
    assert tef.header.v2_title == "Foggy Mountain Breakdown"
    assert tef.header.v2_time_num == 4
    assert tef.header.v2_time_denom == 4
    assert tef.header.v2_strings == 14  # Total across all tracks
    assert tef.header.v2_tracks == 3

    # Check instruments
    assert len(tef.instruments) == 3
    mandolin = tef.instruments[0]
    assert "Mandolin" in mandolin.name
    assert mandolin.num_strings == 4

    # Check notes
    assert len(tef.note_events) > 100
    # Notes should be distributed across tracks
    track_counts = {}
    for evt in tef.note_events:
        track_counts[evt.track] = track_counts.get(evt.track, 0) + 1
    assert len(track_counts) >= 2  # At least 2 tracks have notes

    # V2 notes have 6-byte raw data
    for evt in tef.note_events:
        assert len(evt.raw_data) == 6
