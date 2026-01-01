"""OTF (Open Tab Format) exporter for TEF files."""

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from .reader import TEFFile, TEFNoteEvent, TEFInstrument


# MIDI note to pitch name conversion
MIDI_TO_PITCH = {
    24: "C1", 25: "C#1", 26: "D1", 27: "D#1", 28: "E1", 29: "F1", 30: "F#1", 31: "G1", 32: "G#1", 33: "A1", 34: "A#1", 35: "B1",
    36: "C2", 37: "C#2", 38: "D2", 39: "D#2", 40: "E2", 41: "F2", 42: "F#2", 43: "G2", 44: "G#2", 45: "A2", 46: "A#2", 47: "B2",
    48: "C3", 49: "C#3", 50: "D3", 51: "D#3", 52: "E3", 53: "F3", 54: "F#3", 55: "G3", 56: "G#3", 57: "A3", 58: "A#3", 59: "B3",
    60: "C4", 61: "C#4", 62: "D4", 63: "D#4", 64: "E4", 65: "F4", 66: "F#4", 67: "G4", 68: "G#4", 69: "A4", 70: "A#4", 71: "B4",
    72: "C5", 73: "C#5", 74: "D5", 75: "D#5", 76: "E5", 77: "F5", 78: "F#5", 79: "G5", 80: "G#5", 81: "A5", 82: "A#5", 83: "B5",
}


def midi_to_pitch_name(midi: int) -> str:
    """Convert MIDI note number to pitch name (e.g., 62 -> 'D4')."""
    return MIDI_TO_PITCH.get(midi, f"MIDI{midi}")


@dataclass
class OTFNote:
    """A single note in OTF format."""
    s: int           # String number (1 = highest pitch)
    f: int           # Fret number (0 = open)
    tech: str | None = None  # Technique code (h, p, /, etc.)
    dur: int | None = None   # Duration in ticks (for sustained notes)


@dataclass
class OTFEvent:
    """A note event at a specific tick position."""
    tick: int
    notes: list[OTFNote] = field(default_factory=list)


@dataclass
class OTFMeasure:
    """A measure containing note events."""
    measure: int
    events: list[OTFEvent] = field(default_factory=list)


@dataclass
class OTFTrack:
    """A track/instrument in OTF format."""
    id: str
    instrument: str
    tuning: list[str]
    capo: int = 0
    role: str = "lead"


@dataclass
class OTFTiming:
    """Timing configuration."""
    ticks_per_beat: int = 480


@dataclass
class OTFMetadata:
    """Song metadata."""
    title: str = ""
    composer: str | None = None
    arranger: str | None = None
    key: str | None = None
    time_signature: str = "4/4"
    tempo: int = 120


@dataclass
class OTFReadingListEntry:
    """Reading list entry for playback order."""
    from_measure: int
    to_measure: int


@dataclass
class OTFDocument:
    """Complete OTF document."""
    otf_version: str = "1.0"
    metadata: OTFMetadata = field(default_factory=OTFMetadata)
    timing: OTFTiming = field(default_factory=OTFTiming)
    tracks: list[OTFTrack] = field(default_factory=list)
    notation: dict[str, list[OTFMeasure]] = field(default_factory=dict)
    reading_list: list[OTFReadingListEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML/JSON serialization."""
        result = {
            "otf_version": self.otf_version,
            "metadata": {
                "title": self.metadata.title,
                "time_signature": self.metadata.time_signature,
                "tempo": self.metadata.tempo,
            },
            "timing": {
                "ticks_per_beat": self.timing.ticks_per_beat,
            },
            "tracks": [],
            "notation": {},
        }

        # Add optional metadata
        if self.metadata.composer:
            result["metadata"]["composer"] = self.metadata.composer
        if self.metadata.key:
            result["metadata"]["key"] = self.metadata.key

        # Add tracks
        for track in self.tracks:
            result["tracks"].append({
                "id": track.id,
                "instrument": track.instrument,
                "tuning": track.tuning,
                "capo": track.capo,
                "role": track.role,
            })

        # Add notation per track
        for track_id, measures in self.notation.items():
            result["notation"][track_id] = []
            for measure in measures:
                m = {"measure": measure.measure, "events": []}
                for event in measure.events:
                    e = {"tick": event.tick, "notes": []}
                    for note in event.notes:
                        n = {"s": note.s, "f": note.f}
                        if note.tech:
                            n["tech"] = note.tech
                        if note.dur:
                            n["dur"] = note.dur
                        e["notes"].append(n)
                    m["events"].append(e)
                result["notation"][track_id].append(m)

        # Add reading list if present
        if self.reading_list:
            result["reading_list"] = [
                {"from_measure": e.from_measure, "to_measure": e.to_measure}
                for e in self.reading_list
            ]

        return result

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        try:
            import yaml
            return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False, allow_unicode=True)
        except ImportError:
            # Fallback to JSON if yaml not available
            return self.to_json()

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def instrument_to_otf_id(inst: TEFInstrument) -> str:
    """Generate a clean ID from instrument name."""
    name = inst.name.lower()
    # Remove common suffixes
    for suffix in [" open g", " standard", " gdae", " gda"]:
        name = name.replace(suffix, "")
    # Replace spaces with hyphens
    name = name.replace(" ", "-")
    return name


def instrument_to_type(inst: TEFInstrument) -> str:
    """Map instrument name to standard type identifier."""
    name = inst.name.lower()
    if "banjo" in name:
        return "5-string-banjo"
    elif "mandolin" in name:
        return "mandolin"
    elif "guitar" in name:
        return "6-string-guitar"
    elif "bass" in name:
        return "upright-bass"
    elif "dobro" in name or "resonator" in name:
        return "dobro"
    elif "fiddle" in name or "violin" in name:
        return "fiddle"
    else:
        return f"{inst.num_strings}-string"


def technique_from_event(event: TEFNoteEvent) -> str | None:
    """Map TEF articulation to OTF technique code."""
    art = event.extra  # In new format, articulation is stored elsewhere
    marker = event.marker

    # Check marker first
    if marker == 'L':  # Legato
        # Could be hammer-on or pull-off based on context
        # For now, mark as legato
        return "h"  # Default to hammer-on for legato

    # Check articulation byte from raw_data if available
    if event.raw_data and len(event.raw_data) > 5:
        art_byte = event.raw_data[5]
        if art_byte == 1:
            return "h"  # Hammer-on
        elif art_byte == 2:
            return "p"  # Pull-off
        elif art_byte == 3:
            return "/"  # Slide

    return None


def tef_to_otf(tef: TEFFile) -> OTFDocument:
    """Convert a parsed TEF file to OTF format.

    Args:
        tef: Parsed TEF file

    Returns:
        OTFDocument ready for serialization
    """
    doc = OTFDocument()

    # Metadata
    doc.metadata.title = tef.title or tef.path.stem
    if tef.header.is_v2:
        doc.metadata.time_signature = f"{tef.header.v2_time_num}/{tef.header.v2_time_denom}"
        doc.metadata.tempo = tef.header.v2_tempo
        if tef.header.v2_composer:
            doc.metadata.composer = tef.header.v2_composer
    else:
        # V3 defaults
        doc.metadata.time_signature = "2/2"  # Cut time for bluegrass
        doc.metadata.tempo = 160

    # Tracks from instruments
    for inst in tef.instruments:
        track_id = instrument_to_otf_id(inst)
        track = OTFTrack(
            id=track_id,
            instrument=instrument_to_type(inst),
            tuning=[midi_to_pitch_name(p) for p in inst.tuning_pitches],
            role="lead" if "banjo" in inst.name.lower() or "mandolin" in inst.name.lower() else "rhythm",
        )
        doc.tracks.append(track)

    # Group note events by track and measure
    # TEF position is in 16th note grid, 16 positions per measure
    # In 2/2 (cut time): 2 beats per measure * 480 ticks/beat = 960 ticks/measure
    # 960 ticks / 16 positions = 60 ticks per position
    TICKS_PER_POSITION = 60
    POSITIONS_PER_MEASURE = 16

    track_events: dict[str, dict[int, list[tuple[int, TEFNoteEvent]]]] = {}

    for event in tef.note_events:
        if not event.is_melody:
            continue

        # Get track ID
        if event.track < len(doc.tracks):
            track_id = doc.tracks[event.track].id
        else:
            track_id = "unknown"

        if track_id not in track_events:
            track_events[track_id] = {}

        # Calculate measure and tick within measure
        measure = (event.position // POSITIONS_PER_MEASURE) + 1
        position_in_measure = event.position % POSITIONS_PER_MEASURE
        tick = position_in_measure * TICKS_PER_POSITION

        if measure not in track_events[track_id]:
            track_events[track_id][measure] = []

        track_events[track_id][measure].append((tick, event))

    # Build notation structure
    for track_id, measures in track_events.items():
        doc.notation[track_id] = []

        for measure_num in sorted(measures.keys()):
            events = measures[measure_num]

            # Group events by tick position (for chords)
            events_by_tick: dict[int, list[TEFNoteEvent]] = {}
            for tick, evt in events:
                if tick not in events_by_tick:
                    events_by_tick[tick] = []
                events_by_tick[tick].append(evt)

            otf_measure = OTFMeasure(measure=measure_num)

            for tick in sorted(events_by_tick.keys()):
                otf_event = OTFEvent(tick=tick)

                for evt in events_by_tick[tick]:
                    result = evt.decode_string_fret()
                    if result:
                        string, fret = result
                        tech = technique_from_event(evt)
                        note = OTFNote(s=string, f=fret, tech=tech)
                        otf_event.notes.append(note)

                if otf_event.notes:
                    otf_measure.events.append(otf_event)

            if otf_measure.events:
                doc.notation[track_id].append(otf_measure)

    # Reading list
    for entry in tef.reading_list:
        doc.reading_list.append(OTFReadingListEntry(
            from_measure=entry.from_measure,
            to_measure=entry.to_measure,
        ))

    return doc
