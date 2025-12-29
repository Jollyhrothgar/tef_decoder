"""Binary reader for TEF files."""

from dataclasses import dataclass, field
from pathlib import Path
import struct


@dataclass
class TEFHeader:
    """TEF file header information."""
    format_id: int          # Bytes 0-1: format identifier (0x0010)
    version_major: int      # Byte 3: major version
    version_minor: int      # Byte 2: minor version
    raw_header: bytes       # First 64 bytes for analysis

    @property
    def version(self) -> str:
        return f"{self.version_major}.{self.version_minor:02d}"


@dataclass
class TEFString:
    """A string extracted from the TEF file."""
    offset: int
    value: str
    length: int


@dataclass
class TEFInstrument:
    """Instrument definition from TEF file."""
    name: str
    tuning_name: str
    num_strings: int
    tuning_pitches: list[int]  # MIDI note numbers
    offset: int


@dataclass
class TEFChord:
    """Chord definition from TEF file."""
    name: str
    offset: int


@dataclass
class TEFSection:
    """Section marker (e.g., "A Part", "B Part")."""
    name: str
    offset: int


@dataclass
class TEFNoteEvent:
    """A note event from the TEF file.

    12-byte record structure (large file / event list format):
    - Bytes 0-1: Position (tick count, little-endian). Multiply by ~40 for MIDI ticks.
    - Byte 2: Always 0
    - Byte 3: Track/voice ID (1=melody, 3=bass?, 4=accompaniment?)
    - Byte 4: Marker type (0x49='I', 0x46='F', 0x4C='L', 0x00='S')
    - Byte 5: Articulation (0=normal, 1=hammer-on, 2=pull-off, 3=slide)
    - Bytes 6-8: Always 0
    - Byte 9: Module/voice (0=accompaniment, 6/12/18=melody voices)
    - Byte 10: Always 0
    - Byte 11: Combined string+fret encoding for melody notes
    """
    position: int          # Tick position (multiply by ~40 for MIDI ticks)
    track: int             # Track/module ID
    marker: str            # 'I'=Initial, 'F'=Fret, 'L'=Legato, 'S'=Special
    extra: int             # Articulation: 0=normal, 1=hammer-on, 2=pull-off, 3=slide
    pitch_byte: int        # Byte 9 - module/voice (0, 6, 12, or 18)
    raw_data: bytes        # Full 12-byte record for analysis

    @property
    def articulation(self) -> str:
        """Human-readable articulation type."""
        return {0: 'normal', 1: 'hammer-on', 2: 'pull-off', 3: 'slide'}.get(self.extra, 'unknown')

    @property
    def b6(self) -> int:
        """Byte 6 - contains string encoding in lower bits."""
        return self.raw_data[6] if len(self.raw_data) > 6 else 0

    @property
    def b9(self) -> int:
        """Byte 9 - module/voice indicator (0=accompaniment, 6/12/18=melody)."""
        return self.pitch_byte

    @property
    def b10(self) -> int:
        """Byte 10 - fret encoding (fret + 1)."""
        return self.raw_data[10] if len(self.raw_data) > 10 else 0

    @property
    def b11(self) -> int:
        """Byte 11 value - used in large file format."""
        return self.raw_data[11] if len(self.raw_data) > 11 else 0

    @property
    def is_melody(self) -> bool:
        """True if this is a melody note (can decode string/fret)."""
        # Unified format: check if byte 10 (fret + 1) is valid
        if len(self.raw_data) >= 12 and self.raw_data[10] > 0:
            # Also verify string encoding is valid (bits 3-5 of byte 6)
            b6 = self.raw_data[6]
            string_val = b6 & 0x38  # Bits 3-5 only
            if string_val in (0, 8, 16, 24, 32):
                return True
        return False

    def decode_string_fret(self) -> tuple[int, int] | None:
        """Decode string and fret from note record.

        Returns (string, fret) tuple where string is 1-5 and fret is 0+.
        Returns None if decoding fails.

        Unified format (all TEF files):
        - Byte 6: Position low byte with string encoded in bits 0-5
          (values 0, 8, 16, 24, 32 map to strings 1-5)
          Bits 6-7 are position high bits, not string data
        - Byte 10: Fret + 1
        - Byte 11: Marker (I, F, L)
        """
        if len(self.raw_data) < 12:
            return None

        # String from byte 6, bits 0-5 (values 0, 8, 16, 24, 32)
        # Bits 6-7 are position extension, mask them off
        b6 = self.raw_data[6]
        string_val = b6 & 0x38  # Bits 3-5 only (0x38 = 0b00111000)

        # Valid string encodings: 0, 8, 16, 24, 32 -> strings 1-5
        if string_val not in (0, 8, 16, 24, 32):
            return None

        string = string_val // 8 + 1

        # Fret from byte 10 (value - 1)
        fret = self.raw_data[10] - 1

        # Validate ranges
        if not (1 <= string <= 5) or fret < 0 or fret > 24:
            return None

        return (string, fret)

    def get_pitch(self, tuning: list[int] | None = None) -> int | None:
        """Calculate MIDI pitch from string/fret.

        Args:
            tuning: List of MIDI pitches for each string (default: Open G banjo)
                    [D4=62, B3=59, G3=55, D3=50, g4=67]
        """
        if tuning is None:
            tuning = [62, 59, 55, 50, 67]  # Open G banjo: D4, B3, G3, D3, g4

        result = self.decode_string_fret()
        if result is None:
            return None

        string, fret = result
        if string < 1 or string > len(tuning):
            return None

        return tuning[string - 1] + fret


@dataclass
class TEFFile:
    """Parsed TEF file contents."""
    path: Path
    header: TEFHeader
    title: str = ""
    strings: list[TEFString] = field(default_factory=list)
    instruments: list[TEFInstrument] = field(default_factory=list)
    chords: list[TEFChord] = field(default_factory=list)
    sections: list[TEFSection] = field(default_factory=list)
    note_events: list[TEFNoteEvent] = field(default_factory=list)

    def dump(self) -> str:
        """Return a human-readable dump of the file contents."""
        lines = [
            f"TEF File: {self.path.name}",
            f"Version:  {self.header.version}",
            f"Title:    {self.title}",
            "",
            "Instruments:",
        ]
        for inst in self.instruments:
            pitches = ", ".join(str(p) for p in inst.tuning_pitches)
            lines.append(f"  - {inst.name} ({inst.num_strings} strings): [{pitches}]")

        if self.sections:
            lines.append("")
            lines.append("Sections:")
            for sec in self.sections:
                lines.append(f"  - {sec.name}")

        if self.chords:
            lines.append("")
            lines.append("Chords:")
            chord_names = [c.name for c in self.chords]
            lines.append(f"  {', '.join(chord_names)}")

        if self.note_events:
            lines.append("")
            lines.append(f"Note Events: {len(self.note_events)} events")

            # Count melody vs accompaniment
            melody_events = [e for e in self.note_events if e.is_melody]
            accomp_events = [e for e in self.note_events if not e.is_melody]
            lines.append(f"  Melody: {len(melody_events)}, Accompaniment: {len(accomp_events)}")

            # Decode stats
            decoded = [e for e in melody_events if e.decode_string_fret() is not None]
            lines.append(f"  Successfully decoded: {len(decoded)}/{len(melody_events)} melody notes")

            # Group by position to show structure
            positions = {}
            for evt in self.note_events:
                positions.setdefault(evt.position, []).append(evt)
            lines.append(f"  Unique positions: {len(positions)}")

            # Show first few with decoded info
            lines.append("  First 15 melody notes:")
            shown = 0
            for evt in self.note_events:
                if not evt.is_melody:
                    continue
                result = evt.decode_string_fret()
                if result:
                    string, fret = result
                    pitch = evt.get_pitch()
                    art = f" ({evt.articulation})" if evt.extra != 0 else ""
                    lines.append(f"    tick {evt.position:4d}: s{string} f{fret} = MIDI {pitch}{art}")
                else:
                    lines.append(f"    tick {evt.position:4d}: [decode failed] b9={evt.b9} b11={evt.b11}")
                shown += 1
                if shown >= 15:
                    break

        return "\n".join(lines)


class TEFReader:
    """Reader for TablEdit .tef files."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.pos = 0

    def read_header(self) -> TEFHeader:
        """Parse the TEF header."""
        raw = self.data[:64]
        format_id = struct.unpack("<H", raw[0:2])[0]
        version_minor = raw[2]
        version_major = raw[3]

        return TEFHeader(
            format_id=format_id,
            version_major=version_major,
            version_minor=version_minor,
            raw_header=raw,
        )

    def find_strings(self) -> list[TEFString]:
        """Find all readable strings in the file.

        TEF uses 2-byte little-endian length prefix followed by string data.
        Some strings are null-terminated, some are not.
        """
        strings = []
        i = 0
        while i < len(self.data) - 2:
            # Try 2-byte length prefix (little-endian)
            length = struct.unpack("<H", self.data[i:i+2])[0]
            if 3 <= length <= 100 and i + 2 + length <= len(self.data):
                candidate = self.data[i + 2:i + 2 + length]
                # Strip trailing null if present
                if candidate and candidate[-1] == 0:
                    candidate = candidate[:-1]
                # Check if it's printable ASCII (including common punctuation)
                if candidate and all(32 <= b < 127 or b in (0,) for b in candidate):
                    try:
                        value = candidate.decode('ascii').rstrip('\x00')
                        # Filter: require at least one letter, not all digits
                        if value and any(c.isalpha() for c in value):
                            strings.append(TEFString(offset=i, value=value, length=length))
                            i += 2 + length
                            continue
                    except UnicodeDecodeError:
                        pass
            i += 1
        return strings

    def find_section_marker(self, marker: bytes = b"debtG") -> int:
        """Find the section marker offset."""
        idx = self.data.find(marker)
        return idx if idx >= 0 else -1

    def parse_instruments(self) -> list[TEFInstrument]:
        """Parse instrument definitions from the file.

        Instrument records appear in a specific region (~0x2f0-0x3c0) with structure:
        - [record_header][tuning_bytes][velocity_bytes][instrument_name]
        - Tuning bytes are distinct values; velocity bytes are all the same value
        """
        instruments = []

        # Instrument names with expected string counts
        instrument_info = [
            (b"Banjo open G", 5),
            (b"guitar", 6),
            (b"bass", 4),
        ]

        for name_bytes, expected_strings in instrument_info:
            idx = self.data.find(name_bytes)
            if idx < 0:
                continue

            name = name_bytes.decode('ascii')

            # The bytes before the name are: [tuning * n][velocity * n] or just [tuning * n][nulls]
            # We need to skip velocity/padding and find tuning
            # Tuning is at offset: idx - n - n (for velocity) or idx - n - nulls

            # Look back from the name to find the tuning bytes
            # Pattern: tuning bytes are varied, velocity bytes are uniform
            pos = idx - 1

            # Skip nulls
            while pos > 0 and self.data[pos] == 0:
                pos -= 1

            # Check if we have uniform bytes (velocity field) - skip all of them
            if pos >= expected_strings - 1:
                uniform_val = self.data[pos]
                if uniform_val != 0:  # Not null padding
                    uniform_count = 0
                    check_pos = pos
                    while check_pos > 0 and self.data[check_pos] == uniform_val:
                        uniform_count += 1
                        check_pos -= 1

                    if uniform_count >= 4:  # At least 4 uniform bytes = velocity field
                        pos -= uniform_count

            # Skip any isolated bytes and nulls before tuning
            while pos > 0 and (self.data[pos] == 0 or pos > 0 and self.data[pos - 1] == 0):
                pos -= 1

            # Now extract tuning bytes - they should be in the valid MIDI range
            tuning_end = pos + 1
            tuning_start = tuning_end - expected_strings
            if tuning_start >= 0:
                tuning_bytes = list(self.data[tuning_start:tuning_end])
            else:
                tuning_bytes = []

            instruments.append(TEFInstrument(
                name=name,
                tuning_name="",
                num_strings=expected_strings,
                tuning_pitches=tuning_bytes,
                offset=idx,
            ))

        return instruments

    def parse_chords(self) -> list[TEFChord]:
        """Parse chord symbols from the file."""
        chords = []

        # Look for common chord patterns
        # Chords appear as length-prefixed strings in a specific region
        strings = self.find_strings()

        chord_patterns = {'C', 'D', 'E', 'F', 'G', 'A', 'B'}
        for s in strings:
            # Chord names: start with note letter, may have modifiers
            if s.value and s.value[0] in chord_patterns:
                # Filter: short, no spaces (not a title)
                if len(s.value) <= 10 and ' ' not in s.value:
                    # Additional filter: common chord suffixes
                    if len(s.value) == 1 or any(
                        s.value[1:].startswith(suf)
                        for suf in ['m', '7', 'maj', 'min', 'dim', 'aug', '#', 'b', 'sus']
                    ):
                        chords.append(TEFChord(name=s.value, offset=s.offset))

        return chords

    def parse_sections(self) -> list[TEFSection]:
        """Parse section markers (A Part, B Part, etc.)."""
        sections = []
        strings = self.find_strings()

        for s in strings:
            if 'Part' in s.value or s.value.startswith('(') and s.value.endswith(')'):
                sections.append(TEFSection(name=s.value, offset=s.offset))

        return sections

    def find_debt_offset(self) -> int:
        """Find the note region start using the 'debt' header marker.

        The 'debt' marker is followed by a 4-byte offset value. Notes typically
        start at (debt_value - 6), but some files have notes at (debt_value + 6).

        Returns the note region start offset, or -1 if not found.
        """
        debt_pos = self.data.find(b'debt')
        if debt_pos < 0:
            return -1

        # Read the 4-byte value after 'debt'
        debt_val = struct.unpack('<I', self.data[debt_pos + 4:debt_pos + 8])[0]

        # Valid markers: I, F, L, C (C is used for chords/continue in some files)
        valid_markers = (0x49, 0x46, 0x4c, 0x43)

        # Try different offsets from debt_val
        for offset in [-6, 0, 6, 12]:
            note_start = debt_val + offset
            if note_start + 24 <= len(self.data) and note_start >= 0:
                rec1 = self.data[note_start:note_start + 12]
                rec2 = self.data[note_start + 12:note_start + 24]
                # Check if either record has a valid marker at byte 11
                if rec1[11] in valid_markers or rec2[11] in valid_markers:
                    return note_start

        return -1

    def find_note_region(self) -> tuple[int, str]:
        """Find the start offset of the note event region and format type.

        Uses the unified format discovered via the 'debt' header:
        - All files use 12-byte records with marker at byte 11
        - String encoded in bits 3-5 of position low byte (byte 6)
        - Fret in byte 10 (value - 1)
        - Position in bytes 6-7 (low bytes) or extended with 0-5 for larger positions

        Returns (offset, 'unified') or (-1, '') if not found.
        """
        # Try the debt header approach first
        offset = self.find_debt_offset()
        if offset >= 0:
            return (offset, 'unified')

        # Fallback: search for marker pattern at byte 11
        for start in range(0x400, len(self.data) - 24, 4):
            rec1 = self.data[start:start+12]
            rec2 = self.data[start+12:start+24]

            if len(rec1) < 12 or len(rec2) < 12:
                continue

            # Check for valid markers at byte 11
            if (rec1[11] in (0x49, 0x46, 0x4c) and
                rec2[11] in (0x49, 0x46, 0x4c)):
                return (start, 'unified')

        return (-1, '')

    def parse_note_events(self, start_offset: int = -1) -> list[TEFNoteEvent]:
        """Parse note events from the file.

        Note events are 12-byte records with unified format:
        - Bytes 0-5: Extended position/flags (may be zeros for simple files)
        - Byte 6: Position low byte (also contains string encoding in bits 3-5)
        - Byte 7: Position high byte
        - Bytes 8-9: Additional flags
        - Byte 10: Fret + 1
        - Byte 11: Marker ('I'=Initial, 'F'=Fret, 'L'=Legato)

        String encoding: string = (byte6 & 0x38) >> 3 + 1  (values 0,8,16,24,32 map to strings 1-5)
        """
        events = []
        format_type = 'unified'

        # Find note region if not specified
        if start_offset < 0:
            start_offset, format_type = self.find_note_region()
            if start_offset < 0:
                return events  # No notes found

        offset = start_offset
        prev_pos = -1

        while offset + 12 <= len(self.data):
            record = self.data[offset:offset + 12]

            # Unified format: marker at byte 11
            marker_byte = record[11]

            # Decode marker
            if marker_byte == 0x49:  # 'I'
                marker = 'I'
            elif marker_byte == 0x46:  # 'F'
                marker = 'F'
            elif marker_byte == 0x4c:  # 'L'
                marker = 'L'
            elif marker_byte == 0x43:  # 'C' - chord/continue marker
                marker = 'C'
            elif marker_byte == 0x40:  # '@' - special marker in some files
                marker = '@'
            elif marker_byte == 0x00:
                marker = 'S'  # Special/section marker
            else:
                # Invalid marker - end of note region
                break

            # Position from bytes 6-7 only (bytes 0-5 contain flags/articulation, not position)
            pos_low = struct.unpack("<H", record[6:8])[0]

            # Clear the string encoding bits from position (bits 0-5 of low byte)
            pos = pos_low & 0xFFC0

            # Track/voice info from bytes 4-5
            track = record[4] if record[4] != 0 else 1
            extra = record[5]  # Articulation: 0=normal, 1=hammer-on, 2=pull-off, 3=slide

            # For backward compatibility, keep pitch_byte (was b9 in old format)
            pitch_byte = record[9]

            # Stop if we see end marker pattern
            if record[6:8] == b'\xff\xff' or record[10:12] == b'\xff\xff':
                break

            # Stop if position jumps way back (likely end of region)
            if prev_pos >= 0 and pos < prev_pos - 1000 and pos == 0:
                break

            events.append(TEFNoteEvent(
                position=pos,
                track=track,
                marker=marker,
                extra=extra,
                pitch_byte=pitch_byte,
                raw_data=record,
            ))

            prev_pos = pos
            offset += 12

        return events

    def parse(self) -> TEFFile:
        """Parse the entire TEF file."""
        header = self.read_header()
        strings = self.find_strings()

        # Find title (usually the longest string early in the file)
        title = ""
        for s in strings:
            if s.offset < 0x200 and len(s.value) > len(title):
                # Skip common non-title strings
                if 'Part' not in s.value and not s.value.startswith('('):
                    title = s.value

        instruments = self.parse_instruments()
        chords = self.parse_chords()
        sections = self.parse_sections()
        note_events = self.parse_note_events()

        return TEFFile(
            path=self.path,
            header=header,
            title=title,
            strings=strings,
            instruments=instruments,
            chords=chords,
            sections=sections,
            note_events=note_events,
        )
