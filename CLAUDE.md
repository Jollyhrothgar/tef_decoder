# TablEdit Reverse Engineering Project

Reverse engineering the TablEdit `.tef` file format to preserve millions of tablature arrangements before the software becomes unsupported.

## Project Goal

Create a parser that can read `.tef` files and export music data in open formats (ABC notation, LilyPond, MIDI, MusicXML) - enabling archival, format conversion, and long-term preservation of user-created tablature.

## Development Practices

- **Test-driven development** - write tests, especially for parser changes
- **Best practices**: DRY, KISS - avoid over-engineering
- **Python**: Always use `uv run` (e.g., `uv run pytest`, `uv run python script.py`)
- **Scripts to Rule Them All**: Use standardized scripts for core operations (see below)

## Quick Start

```bash
./scripts/bootstrap              # Install deps + extract PDF docs
./scripts/utility parse sample.tef   # Parse a TEF file
uv run pytest                    # Run tests
```

## Project Structure

```
TablEdit_Reverse/
├── CLAUDE.md              # This file
├── docs/                  # Documentation extracted from PDF
├── samples/               # Sample .tef files for testing
│   └── shuck_the_corn/    # Reference file with known exports
├── src/
│   ├── tef_parser/        # Core parser implementation
│   │   ├── __init__.py
│   │   ├── reader.py      # Binary file reader
│   │   ├── structures.py  # Data structures for TEF elements
│   │   └── decoder.py     # Note/tablature decoding logic
│   └── exporters/         # Export format writers
│       ├── abc.py         # ABC notation export
│       ├── lilypond.py    # LilyPond export
│       ├── midi.py        # MIDI export
│       └── musicxml.py    # MusicXML export
├── tests/                 # Test suite
│   ├── test_parser.py
│   └── test_exporters.py
└── scripts/               # Scripts to Rule Them All
    ├── bootstrap          # First-time setup
    ├── server             # Start dev tools (hex viewer, etc.)
    ├── utility            # User-facing commands
    └── lib/               # Python implementations
        ├── extract_pdf.py
        ├── parse_tef.py
        └── export.py
```

## Scripts to Rule Them All

Standardized entry points for all operations. Bash wrappers delegate to Python in `scripts/lib/`.

### bootstrap

First-time setup. Safe to run anytime.

```bash
./scripts/bootstrap           # Full setup: uv sync + extract PDF docs
./scripts/bootstrap --quick   # Skip dependency install
```

### server

Start development tools.

```bash
./scripts/server              # Start hex viewer / analysis UI (future)
```

### utility

User-facing commands for parsing and exporting.

```bash
./scripts/utility parse <file.tef>              # Parse and dump structure
./scripts/utility export <file.tef> [--pretty]  # Export to JSON
./scripts/utility midi <file.tef> [output.mid]  # Export parsed notes to MIDI
./scripts/utility view <file.tef>               # View as ASCII tablature timeline
./scripts/utility version <file.tef>            # Show file version
```

### Script Template

All scripts follow this pattern:

```bash
#!/usr/bin/env bash
#
# <name> - <description>
#
# Usage:
#   ./scripts/<name> [options]
#

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Delegate to Python implementation
uv run python3 scripts/lib/<implementation>.py "$@"
```

## Reference Files

| File | Purpose |
|------|---------|
| `shuck_the_corn.tef` | Primary test file (8,691 bytes) |
| `shuck_the_corn.abc` | Known-good ABC export for validation |
| `shuck_the_corn.ly` | Known-good LilyPond export for validation |
| `shuck_the_corn.mid` | Known-good MIDI export for validation |
| `temac_e.pdf` | TablEdit documentation (2.9MB) |
| `temac_sections/` | PDF split into 76 section chunks (use pdf_splitter) |
| `tev305.dmg` | TablEdit v3.05 installer (for testing) |

## Test Files

Test files created or collected for validating the parser:

### Single Note Files
| File | Purpose |
|------|---------|
| `single_open_string_1_d4.tef` | Validate string 1 open = D4 (MIDI 62) |
| `single_open_string_2_b3.tef` | Validate string 2 open = B3 (MIDI 59) |
| `single_open_string_3_g3.tef` | Validate string 3 open = G3 (MIDI 55) |
| `single_open_string_4_d3.tef` | Validate string 4 open = D3 (MIDI 50) |
| `single_open_string_5_tg4.tef` | Validate string 5 open = g4 (MIDI 67) |
| `string_1_fret_2_e4.tef` | Validate fret encoding: s1 f2 = E4 (MIDI 64) |
| `string_1_fret_3_f4.tef` | Validate fret encoding: s1 f3 = F4 (MIDI 65) |

### Multi-Note Files
| File | Purpose |
|------|---------|
| `two_simultaneus_notes_string_1_and_5_eigth_notes.tef` | Simultaneous notes on strings 1 and 5 |
| `sequential_3rd_string_quarter_beat_1_eigth_beat_2.tef` | Sequential notes with timing offsets |
| `hammar_on_2nd_string_eight_notes_beat_1_open_beat_and-of-1_fret_2.tef` | Hammer-on articulation test |
| `Multi Note.tef` | 36 notes - simple multi-note sequence |
| `Multi Note 2.tef` | 62 notes - extended multi-note sequence |
| `Multi Note - Two Track Offset.tef` | Two-track file with offset timing |

### Complex Songs
| File | Purpose |
|------|---------|
| `shuck_the_corn.tef` | Primary test - full banjo arrangement (8691 bytes, 570 events) |
| `shuck_the_corn_banjo_only.tef` | Banjo-only version for module/track isolation |
| `angeline_the_baker_banjo_guitar_banjo_fifth_string_tuned_1_step_higher.tef` | Multi-track banjo+guitar, spiked 5th string (G→A) |

### Expected MIDI Outputs
| File | Purpose |
|------|---------|
| `shuck_the_corn.mid` | TablEdit's official MIDI export (full arrangement) |
| `shuck_the_corn_melody.mid` | Melody track only |
| `Multi Note.mid` | Reference MIDI for Multi Note.tef |
| `angeline_the_baker...mid` | Reference MIDI for angeline (188 banjo + guitar notes) |

### Generated Files
| Suffix | Purpose |
|--------|---------|
| `.parsed.mid` | Parser-generated MIDI for comparison |
| `.json` | JSON export of parsed note events |

### Documentation Notes

The PDF is a **user manual** (UI-focused), not a file format specification. Reverse engineering required.

Key insights from documentation:
- **Format versions**: v2 format (pre-3.00) vs v3 format differ; v3 files may have features unsupported in v2
- **File protection**: Files can be password-protected against modification/printing/TEFview
- **Metadata fields**: title, composer, comments, copyright, arranger (see `072_L3_Title Information.pdf`)
- **Structure**: Up to 6 instrument modules + 1 drum module per file
- **Workbooks**: `.tew` files are separate (just file lists, not embedded)

To read documentation sections:
```bash
cd pdf_splitter && uv run python3 -c "
import pymupdf
doc = pymupdf.open('../temac_sections/072_L3_Title Information.pdf')
for page in doc: print(page.get_text())
"
```

## TuxGuitar Reference Implementation (Dec 2025)

**MAJOR DISCOVERY**: TuxGuitar (https://github.com/tuxguitar) has a complete TEF3 parser!
Located at: `/tuxguitar/desktop/TuxGuitar-tef/src/app/tuxguitar/io/tef3/`

### TuxGuitar File Structure Order

Files are read sequentially in this exact order:

```
1. Header              (256 bytes, fixed)
2. Song metadata       (title, author, comments, notes, url, copyright, lyrics, text events)
3. Chord definitions   (if hasChords flag set in header)
4. Measures            (2-byte size + 2-byte count + fixed-size records)
5. Tracks              (instrument definitions with tuning)
6. Print metadata      (page headers/footers)
7. Reading list        (if hasReadingList flag at header offset 128)
8. Components          (12-byte records until 0xFFFFFFFF footer)
```

### TuxGuitar Header Format (256 bytes)

Key offsets from TEInputStream.java:

| Offset | Size | Field | Expected Value |
|--------|------|-------|----------------|
| 3 | 1 | majorVersion | 3 (for TEF v3.x) |
| 6-7 | 2 | initialBpm | tempo |
| 56-59 | 4 | "tbed" | 0x74, 0x62, 0x65, 0x64 |
| 84-87 | 4 | posOfTextEvents | non-zero = has text events |
| 88-91 | 4 | posOfChords | non-zero = has chords |
| 128-131 | 4 | posOfReadingList | non-zero = has reading list |
| 140-143 | 4 | posOfCopyright | non-zero = has copyright |
| 202-203 | 2 | wOldNum | 4 |
| 204 | 1 | wFormatLo | 4 |
| 205 | 1 | wFormatHi | 10 |

**Note**: TuxGuitar checks for "tbed" at offset 56, not "debt" - we had the marker backwards!

### TuxGuitar Reading List Format

```java
// From TEInputStream.java lines 505-525
int sizeOfReadingListEntry = readShort();  // 2 bytes
int totalReadingListEntries = readShort(); // 2 bytes

for each entry:
    int startMeasure = readShort();  // 2 bytes, NOT 1 byte!
    int endMeasure = readShort();    // 2 bytes, NOT 1 byte!
    String name = readNullTerminatedString(sizeOfEntry - 5);
```

**Key difference from our parser**: Measures are 2-byte shorts, not single bytes!

### TuxGuitar Component Format (12 bytes each)

From TEInputStream.java line 527+:

```
Bytes 0-3:  location (4-byte int, little-endian)
Byte 4:     componentType
Bytes 5-11: type-specific data
```

#### Component Types (byte 4):

| Type | Meaning |
|------|---------|
| 0x01-0x19 | Note (fret = (type & 0x1f) - 1) |
| 0x33 | Rest |
| 0x35 | Chord |
| 0x36 | Line break |
| 0x37 | Accent |
| 0x38 | Crescendo |
| 0x39 | Text event |
| 0x3D | Connection |
| 0x75 | Scale diagram |
| 0x78 | Drum change |
| 0x7D | Spacing marker OR grace note metadata |
| 0x7E | Voice change |
| 0xB6 | Symbol |
| 0xB7 | Ending |
| 0xBD | Beam break |
| 0xBE | Stem length |
| 0xFD | Syncopation |
| 0xFE | Tempo change |

### TuxGuitar Position Encoding

From TEPosition.java - the 4-byte location encodes multiple values:

```java
int valuePerString = 8;
int valuePerPositionPerString = 32;
int valuePerPosition = 32 * totalStringCount;  // varies by file!
int maxPositionsInFourFour = 16;  // 16th note grid

// Decode location to (measure, positionInMeasure, string, track):
for each measure:
    timeSignatureRatio = numerator / denominator
    maxPositionsInMeasure = 16 * timeSignatureRatio
    valueForMeasure = valuePerPosition * maxPositionsInMeasure

    if (location <= valueForMeasure):
        positionInMeasure = location / valuePerPosition
        stringOfComponent = (location % valuePerPosition) / valuePerString
        break
    else:
        location -= valueForMeasure
        measureOfComponent++
```

### TuxGuitar Note Component (types 0x01-0x19)

From TEInputStream.java lines 632-680:

```
Byte 4 (type):
  - bits 0-4: fret + 1 (so 0x01 = fret 0, 0x19 = fret 24)
  - bit 6: isGraceNote
  - bit 7: isPitchShifted

Byte 5: bits 0-4 = duration, bits 5-7 = dynamics
Byte 6: bits 0-3 = effect1, bits 4-5 = voice, bits 6-7 = alterations
Byte 7: bits 0-2 = pitchShift, bits 5-7 = graceNoteEffect
Byte 8: bits 0-3 = effect2, bits 4-7 = effect3
Byte 9: bits 0-3 = fontPreset, bit 4 = stabilo
Byte 10: bits 0-4 = fingering, bits 5-7 = stroke
Byte 11: attribute flags
```

### TuxGuitar Tuning Formula (confirmed!)

From TESongParser.java line 135:
```java
string.setValue(96 - tuning[stringIdx]);
```

This matches our discovered formula: `MIDI_pitch = 96 - tuning_byte`

### Implications for Our Parser

Our current parser has fundamental differences from TuxGuitar's:

1. **File navigation**: We search for "debt" marker; TuxGuitar reads sequentially
2. **Component format**: We expected marker at byte 11; TuxGuitar has type at byte 4
3. **Position encoding**: We used bytes 6-7; TuxGuitar uses 4-byte location at bytes 0-3
4. **Fret encoding**: We used byte 10; TuxGuitar encodes fret in component type bits 0-4
5. **Reading list**: We parsed 1-byte measures; TuxGuitar uses 2-byte shorts

This suggests our parser accidentally works for some files but isn't following the actual format.

---

## TEF File Format (Initial Analysis)

### Header Structure (offset 0x00)
```
Offset  Bytes     Meaning
------  --------  ------------------------------------------
0-1     10 00     Format ID (0x0010 = 16)
2       XX        Minor version (e.g., 05 = .05)
3       YY        Major version (e.g., 03 = 3)
4-5     b4 00     Unknown (flags? 0x00b4 = 180)
6-7     a0 00     Unknown
...
38-3B   "debtG"   Section marker
3C+     ...       Offset table begins
```

**Version extraction**: `f"{header[3]}.{header[2]:02d}"` → "3.05"

### Version-Partitioned Testing

TEF format may vary between versions. Organize test fixtures by version:

```
samples/
├── v2.xx/          # Older format files
├── v3.00-3.04/     # Pre-3.05 files
├── v3.05/          # Current known version
│   └── shuck_the_corn/
└── v3.xx-future/   # Newer versions as discovered
```

Version detection enables:
- Conditional parsing logic per format version
- Regression tests scoped to specific versions
- Clear documentation of format evolution

### Known Sections
- **Metadata**: Title at ~0x100 (length-prefixed string)
- **Section markers**: "(A Part)", "(B Part)" - structure annotations
- **Chords**: "C7", "G", "D", etc. with position data
- **Instruments**: "Banjo open G", "guitar", "bass" with tuning info
- **Note data**: Structured records starting ~0x600

### String Encoding
- Length-prefixed strings (1-byte length + ASCII data)
- Some null-terminated strings visible

### Note Data Format (decoded)
Note events start at offset 0x648 (after instrument definitions).

**12-byte record structure:**
```
Offset  Size  Field           Values/Notes
------  ----  -----           ------------
0-1     2     Position        Tick count (little-endian). Multiply by ~40 for MIDI ticks.
2       1     (always 0)
3       1     Track ID        1=melody/main, 3=bass?, 4=accompaniment?, 6/9=other
4       1     Marker          0x49='I', 0x46='F', 0x4C='L', 0x00='S'
5       1     Articulation    0=normal, 1=hammer-on, 2=pull-off, 3=slide
6-8     3     (always 0)
9       1     Pitch-related   Values observed: 0, 6, 12, 18 (multiples of 6)
10      1     (always 0)
11      1     Additional      Possibly encodes string/timing offset (b11/8 values vary)
```

**Marker types:**
- `I` (0x49): Initial note - first struck note at a time position
- `F` (0x46): Fret note - additional picked notes (chord members, roll notes)
- `L` (0x4c): Legato note - slurs, hammer-ons, pull-offs (articulated but not picked)
- `S` (0x00): Special marker - section boundaries, repeats

**Articulation encoding (byte 5):**
| Value | Meaning    | Description |
|-------|------------|-------------|
| 0     | Normal     | Standard picked note |
| 1     | Hammer-on  | Left-hand note attack (ascending) |
| 2     | Pull-off   | Left-hand note attack (descending) |
| 3     | Slide      | Glide between frets |

**Full Effect Encoding (TuxGuitar-verified):**

From TEComponentNote.java - effects are encoded in component bytes 6 and 8:

| Effect1 (byte 6 bits 0-3) | Value | Description |
|---------------------------|-------|-------------|
| HammerOn | 1 | Hammer-on |
| PullOff | 2 | Pull-off |
| Slide | 3 | Slide between frets |
| Choke | 4 | String choke/mute |
| Brush | 5 | Brush stroke |
| NaturalHarmonic | 6 | Natural harmonic |
| ArtificialHarmonic | 7 | Artificial harmonic |
| PalmMute | 8 | Palm mute |
| Tap | 9 | Tap technique |
| Vibrato | 10 | Vibrato |
| Tremolo | 11 | Tremolo picking |
| Bend | 12 | Bend |
| BendRelease | 13 | Bend and release |
| Roll | 14 | Roll |
| DeadNote | 15 | Dead/muted note |

| Effect2 (byte 8 bits 0-3) | Value | Description |
|---------------------------|-------|-------------|
| LetRing | 1 | Let ring |
| Slap | 2 | Slap technique |
| GhostNote | 4 | Ghost note |
| Staccato | 7 | Staccato |
| FadeIn | 8 | Fade in |

**Example from sample file:**
```
tick    3: 1 events [I]      - single note (G3)
tick   30: 6 events [SSLFFF] - includes slide articulation
tick   37: 5 events [IFFFF]  - chord/roll (1 initial + 4 fret notes)
```

**Pitch decoding (INCOMPLETE):**
The formula `43 + pitch_byte` works for some notes but not all. The pitch encoding
appears more complex, possibly involving:
- Byte 9 (pitch_byte): Values 0, 6, 12, 18 seem to encode pitch intervals
- Byte 11: May encode string number or timing offset
- Instrument tuning: Stored as relative values, not absolute MIDI

**Known relationships:**
- MIDI tick ≈ TEF position × 40 (240 ticks/beat MIDI vs ~6 ticks/beat TEF)
- Tuning bytes are relative to first string (intervals match MIDI intervals)
- First note b9=12 → pitch 55 (G3) matches MIDI export

**Module/Instrument encoding (byte 9 - b9):**

Analysis of full vs banjo-only files revealed that b9 indicates the instrument module:

| b9 value | Module | Notes |
|----------|--------|-------|
| 0 | Accompaniment | Guitar, bass - 355 events in full file, 22 in banjo-only |
| 6, 12, 18 | Melody/Lead | Banjo part - identical counts (68, 58, 66) in both files |

Key finding: Removing an instrument from TablEdit (creating banjo-only version) keeps
the b9=6,12,18 event counts identical but shifts their positions. The b9=0 events
are dramatically reduced (from 377 to 22), confirming b9=0 is the accompaniment.

**Status**: 569 note events extracted from sample file.
Record structure decoded. Articulation mapping confirmed.
Module structure discovered (b9 indicates instrument).

### Pitch Encoding Analysis (Dec 2025)

Correlation with TablEdit's MIDI export revealed partial patterns:

**b9 (byte 9) - Module/Voice indicator:**
| b9 value | Module | Meaning |
|----------|--------|---------|
| 0 | Accompaniment | Strummed/arpeggiated patterns on strings 3-5 |
| 6 | Melody voice 1 | Lead notes |
| 12 | Melody voice 2 | Secondary melody |
| 18 | Melody voice 3 | Additional voice |

**b11 (byte 11) - String/Timing encoding:**

The upper nibble (b11 >> 4) correlates with pitch for melody notes:
| Upper nibble | Observed pitch | Formula |
|--------------|----------------|---------|
| 9 | 55 (G3) | ~60 - upper/2 = 55.5 ≈ 55 |
| 13 | 52 (E3) | ~60 - upper/2 = 53.5 ≈ 52 |

For accompaniment (b9=0), multiple upper nibble values (4, 5, 7, 15) produce
the same pitch 67 (G4), suggesting these encode voice/timing slot rather
than pitch directly. The pitch comes from the chord context.

**Verified mappings (from timing correlation with MIDI):**
```
b9=12, b11=152 (upper=9)  → pitch 55 (G3) = string 3 fret 0
b9=6,  b11=216 (upper=13) → pitch 52 (E3) = string 4 fret 2
b9=0,  b11=144 (upper=9)  → pitch 55 (G3) = string 3 fret 0
b9=6,  b11=72  (upper=4)  → pitch 67 (G4) = string 5 fret 0
b9=0,  b11=80  (upper=5)  → pitch 67 (G4) = string 5 fret 0
b9=0,  b11=112 (upper=7)  → pitch 67 (G4) = string 5 fret 0
```

**Current hypothesis:**
- Melody notes (b9 > 0): Upper nibble of b11 encodes string+fret combined
- Accompaniment notes (b9 = 0): Pitch derived from chord context; b11 encodes voice slot

### Unified Note Format (Dec 2025 - BREAKTHROUGH)

**Key Discovery**: All TEF files use the SAME 12-byte note record format. The apparent differences were due to incorrect alignment.

#### The "debt" Header Marker

The `debt` marker at offset 0x38 is crucial for finding notes:

```
Offset 0x38: "debt" followed by 4-byte offset value
```

**Note region location:**
- Primary: `debt_value - 6`
- Some files: `debt_value + 6` (try both, validate by checking for markers)

#### Unified 12-Byte Record Structure

```
Offset  Size  Field           Description
------  ----  -----           -----------
0-5     6     Flags           Articulation/track flags (zeros for simple files)
6       1     Position low    Low byte of position + string in bits 3-5
7       1     Position high   High byte of position
8-9     2     Additional      Reserved/flags
10      1     Fret + 1        Fret number plus one (fret 0 = 0x01)
11      1     Marker          I/F/L/C/S marker type
```

**String encoding (bits 3-5 of byte 6):**
```python
string_val = byte6 & 0x38   # Mask bits 3-5 only
string = string_val // 8 + 1   # Maps 0,8,16,24,32 → strings 1-5
```

| byte[6] & 0x38 | String | Open tuning (Open G) |
|----------------|--------|---------------------|
| 0x00 (0) | 1 | D4 (MIDI 62) |
| 0x08 (8) | 2 | B3 (MIDI 59) |
| 0x10 (16) | 3 | G3 (MIDI 55) |
| 0x18 (24) | 4 | D3 (MIDI 50) |
| 0x20 (32) | 5 | g4 (MIDI 67) |

**Marker types:**
| Marker | Byte | Meaning |
|--------|------|---------|
| I | 0x49 | Initial - first struck note |
| F | 0x46 | Fret - additional picked notes |
| L | 0x4c | Legato - slurs, hammer-ons, pull-offs |
| C | 0x43 | Chord/Continue marker (valid melody note when decodable) |
| @ | 0x40 | Special marker (often bass/thumb notes) |
| A | 0x41 | Articulation marker (valid melody note) |
| & | 0x26 | Another articulation marker (valid melody note) |
| S | 0x00 | Section/special boundary |

**Voice Filtering (byte 8):**

Byte 8 distinguishes between melody voices:
| byte[8] | Meaning | Use |
|---------|---------|-----|
| 0 | Primary melody | Include in melody export |
| 1 | Secondary pattern | Secondary voice/accompaniment |

For melody-only MIDI export, filter by `byte[8] == 0` AND marker in `(I, F, L, @)`.
This produces clean melodic sequences that match the original TablEdit MIDI export.

**Section Storage vs MIDI Playback:**

TEF files store musical **source material** (sections, variations), while MIDI exports
are **rendered arrangements** with repeats unfolded.

| Aspect | TEF Storage | MIDI Export |
|--------|-------------|-------------|
| angeline_the_baker | ~46 beats | ~127 beats |
| Ratio | 1x | 2.75x (repeats) |
| Structure | A-part + B-part stored once | AA+BB+AA... arrangement |

**Section Matching Analysis (angeline_the_baker):**
| Section | TEF Beats | Match Rate | Notes |
|---------|-----------|------------|-------|
| 0 | 0-8 | 100% | Perfect match |
| 1 | 8-16 | 80% | Minor differences |
| 2 | 16-24 | 100% | Perfect match |
| 3 | 24-32 | 100% | Perfect match |
| 4-5 | 32-48 | 10-18% | "High break" variant, not used in MIDI |

**Implication**: TEF parser extracts correct source material. Differences from MIDI
are due to arrangement choices (which sections/repeats TablEdit included in export).

### Reading List (MIDI Playback Order)

**Discovery**: TEF files store a "Reading List" that controls MIDI playback order.
This is the mechanism for repeat expansion and D.S./D.C. handling.

**Location**: Header offset 128 contains a 4-byte pointer to reading list.
If zero, file has no reading list.

**Structure (TuxGuitar-verified):**
```
Reading list header:
  2 bytes: entry_size (typically 32)
  2 bytes: entry_count

Per entry (entry_size bytes each):
  2 bytes: start_measure (little-endian short, 1-indexed)
  2 bytes: end_measure (little-endian short, 1-indexed, inclusive)
  N bytes: name (null-terminated) + padding
```

**Example (angeline_the_baker):**
```
[01] measures 1-8    # A part first time
[02] measures 1-7    # A part repeat (first ending)
[03] measures 9-17   # B part
[04] measures 10-16  # B part variation
[05] measures 18-18  # Ending
```

**Expansion calculation:**
- 8 + 7 + 9 + 7 + 1 = 32 total measures in playback order
- Maps TEF's ~46 beats of source material → MIDI's ~127 beats rendered

**MIDI Export Process:**
1. Parse notes from TEF file (filtered by marker and b8=0)
2. Assign each note to its source measure: `measure = (position // TICKS_PER_MEASURE) + 1`
3. For each reading list entry, output notes from that measure range
4. Calculate output position: cumulative_offset + relative_position

**Measure Timing:**
| Resolution | Ticks per beat | Ticks per measure (4/4) |
|------------|----------------|------------------------|
| High (angeline) | 1408 | 5632 |
| Medium (shuck) | 960 | 3840 |
| Low (Multi Note) | 320 | 1280 |

**Test Results (with reading list expansion):**
| File | Source Notes | Expanded | Original MIDI | Match Rate |
|------|-------------|----------|---------------|------------|
| Multi Note | 36 | 36 (no list) | 36 | **100%** |
| angeline_banjo_only (no RL) | 104 | 104 | 104 | **100%** |
| angeline_banjo_only (with RL) | 104 | 196 | 188 | ~96% (RL mismatch) |

Note: The "with RL" file has an inconsistent reading list - it references measures 9-18
but the banjo-only file only contains notes in measures 1-8. The reading list wasn't
updated when guitar was removed from the original file.

**Decoding formula:**
```python
# Find notes using debt header
debt_pos = data.find(b'debt')
debt_val = struct.unpack('<I', data[debt_pos + 4:debt_pos + 8])[0]
note_start = debt_val - 6   # or +6 for some files

# Decode each 12-byte record
string = (byte[6] & 0x38) // 8 + 1   # Bits 3-5
fret = byte[10] - 1                   # Byte 10 minus 1
marker = byte[11]                     # I/F/L/C/S

# Calculate MIDI pitch
tuning = [62, 59, 55, 50, 67]   # Open G: D4, B3, G3, D3, g4
pitch = tuning[string - 1] + fret
```

**Test results (with strict filter):**
| File | TEF Notes | MIDI Notes | Match Rate | Notes |
|------|-----------|------------|------------|-------|
| Multi Note.tef | 36 | 36 | 100% pitch | All pitches match |
| angeline_banjo_only (no RL) | 104 | 104 | **100%** | Perfect match with A, &, C markers |
| angeline_the_baker | 67 | 188 | 65% | TEF stores source, MIDI has repeats |
| shuck_the_corn.tef | ~50 | varies | High | Correct pitches for first section |

**Timing Scale:**
```python
# TEF uses 1408 ticks per beat, MIDI uses 240
SCALE = 240 / 1408  # = 0.1705
midi_tick = int(tef_position * SCALE)
```

**Why previous analysis was confused:**
- The "simple" and "large" formats were the SAME format at different offsets
- Byte 11 was always the marker - we were just misaligned
- The debt header tells us exactly where to start

### Multi-Note Record Format (Dec 2025)

User-created multi-note test files revealed the complete 12-byte note record structure:

```
Offset  Size  Field         Encoding
------  ----  -----         --------
0       1     Articulation  0=normal, 1=hammer-on source
1-5     5     Reserved      Always zeros
6       1     String+Flags  (string-1)*8 + flags (see below)
7       1     Time offset   Position in half-beat units (0, 1, 2...)
8-9     2     Reserved      Always zeros
10      1     Fret          fret + 1 (so fret 0 = 0x01, fret 2 = 0x03)
11      1     Duration      0x40 + duration_code
```

**byte[6] bit flags:**
| Bits | Meaning |
|------|---------|
| 0-4  | `(string - 1) * 8` (0, 8, 16, 24, 32 for strings 1-5) |
| 6 (0x40) | Hammer-on/pull-off TARGET note |
| 7 (0x80) | Different timing position from first note |

**byte[11] duration codes:**
| Value | Duration |
|-------|----------|
| 0x40  | Default/whole |
| 0x46  | Quarter note |
| 0x49  | Eighth note |

**Verified with multi-note test files:**

| File | Note | byte[0] | byte[6] | byte[7] | byte[10] | byte[11] | Decoded |
|------|------|---------|---------|---------|----------|----------|---------|
| simultaneous | 1 | 0 | 0x00 | 0 | 0x01 | 0x49 | s1 f0 beat1 8th |
| simultaneous | 2 | 0 | 0x20 | 0 | 0x01 | 0x49 | s5 f0 beat1 8th |
| sequential | 1 | 0 | 0x10 | 0 | 0x01 | 0x46 | s3 f0 beat1 qtr |
| sequential | 2 | 0 | 0x90 | 2 | 0x01 | 0x49 | s3 f0 beat2 8th |
| hammer-on | 1 | 0 | 0x08 | 0 | 0x01 | 0x49 | s2 f0 beat1 8th |
| hammer-on | 2 | 1 | 0x48 | 1 | 0x03 | 0x49 | s2 f2 +half 8th HO |

**Key observations:**
- **0x90** = 0x10 (string 3) | 0x80 (different timing flag)
- **0x48** = 0x08 (string 2) | 0x40 (hammer-on target flag)
- **byte[0]=1** marks the SOURCE note of a hammer-on
- **byte[7]=1** = "and of 1" (half beat after beat 1)
- **byte[7]=2** = beat 2 (full beat after beat 1)

### Multi-Track Support

TEF files can contain multiple instrument tracks (up to 6 + drums per the docs).

**TablEdit export behavior:**

| Format | Multi-track? | Notes |
|--------|-------------|-------|
| MIDI | Yes | Separate `MTrk` chunks with instrument names |
| ABC | No | Flattens to single voice |
| LilyPond | No | Exports only selected/primary track |

**For archival**: MIDI is the best TablEdit export format for preserving
multi-track structure. The TEF parser should extract track metadata but
can defer note-per-track parsing to MIDI import.

**ABC multi-voice syntax** (for potential future export):
```abc
V:1 name="Banjo" clef=tab
...notes...
V:2 name="Guitar" clef=tab
...notes...
```

## Implementation Plan

### Phase 1: Documentation & Discovery
1. [ ] Extract text from PDF documentation using pymupdf
2. [ ] Map official file format documentation
3. [ ] Create hex dump annotations for known sections
4. [ ] Build test fixtures from sample files

### Phase 2: Header & Metadata Parser
1. [ ] Parse magic bytes and version detection
2. [ ] Extract title, composer, comments
3. [ ] Parse instrument definitions and tunings
4. [ ] Extract tempo, key, time signature

### Phase 3: Note Data Parser
1. [ ] Decode note event structure
2. [ ] Parse tablature positions (string + fret)
3. [ ] Handle articulations (slides, hammer-ons, bends)
4. [ ] Parse repeat structures and sections

### Phase 4: Export Formats
1. [ ] ABC notation (simplest, good for validation)
2. [ ] MIDI (compare with TablEdit's own export)
3. [ ] LilyPond (preserves tablature layout)
4. [ ] MusicXML (most interoperable)

### Phase 5: Validation & Testing
1. [ ] Round-trip validation against known exports
2. [ ] Test with diverse instrument types (banjo, guitar, bass, mandolin)
3. [ ] Edge cases: complex articulations, multiple voices

## Tools & Dependencies

```bash
# PDF text extraction
uv add pymupdf

# Testing
uv add pytest pytest-cov

# Binary analysis helpers
uv add construct  # For declarative binary parsing

# Export format libraries (as needed)
uv add mido       # MIDI manipulation
```

## Useful Commands

```bash
# Hex dump with ASCII
xxd shuck_the_corn.tef | head -50

# Search for strings in binary
strings shuck_the_corn.tef

# Compare byte ranges
xxd -s 0x100 -l 64 shuck_the_corn.tef
```

## Key Observations from Sample File

### Instrument Definitions (offset ~0x300)
```
Banjo open G: tuning bytes [22 25 29 2e 1d] = gDGBD
guitar:       tuning bytes [20 25 29 2e 33 38] = EADGBE
bass:         tuning bytes [35 3a 3f 44] = EADG
```

**Tuning Formula (Discovered Dec 2025):**
```python
MIDI_pitch = 96 - tuning_byte
```

Verified with Open G banjo tuning:
| Tuning byte | Calculation | MIDI | Note |
|-------------|-------------|------|------|
| 34 (0x22) | 96 - 34 = 62 | 62 | D4 (string 1) |
| 37 (0x25) | 96 - 37 = 59 | 59 | B3 (string 2) |
| 41 (0x29) | 96 - 41 = 55 | 55 | G3 (string 3) |
| 46 (0x2e) | 96 - 46 = 50 | 50 | D3 (string 4) |
| 29 (0x1d) | 96 - 29 = 67 | 67 | G4 (string 5) |

Spiked 5th string (tuned up to A): byte 27 (0x1b) → 96 - 27 = 69 (A4)

### Tempo/Time Signature (offset ~0x3C0)
Time signature 4/4 visible, tempo 160 BPM (matches ABC export)

### Note Events (offset ~0x640+)
Structured 8-byte records containing fret positions, timing, and articulation data. Pattern `XX 02 00 YY ZZ 00 00 00` suggests:
- XX = position (little-endian with next byte)
- YY = note/fret value
- ZZ = string or articulation

## Related Projects

- [PyTablature](https://github.com/search?q=pytablature) - if exists
- [music21](https://web.mit.edu/music21/) - music analysis library
- [ABC notation spec](https://abcnotation.com/wiki/abc:standard:v2.1)

## Success Criteria

A successful parser can:
1. Read any valid .tef file without crashing
2. Extract metadata (title, composer, tempo, key)
3. Extract all note events with correct timing
4. Produce ABC/MIDI output that sounds identical to TablEdit's export
5. Preserve tablature-specific data (string assignments, fret positions)
