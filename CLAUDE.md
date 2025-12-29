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

### Encoding Breakthrough (Dec 2025) - Test Files

User-created test files with single notes revealed the fundamental encoding:

**Small file format (single note, bytes at offset 0x410+):**
```
byte[6]  = (string - 1) * 8    ← STRING encoding
byte[10] = fret + 1            ← FRET encoding
byte[11] = 64 (0x40)           ← base/constant
```

**Verified with test files:**
| File | String | Fret | byte[6] | byte[10] | Decoded |
|------|--------|------|---------|----------|---------|
| string_1_d4.tef | 1 | 0 | 0 | 1 | s1 f0 ✓ |
| string_2_b3.tef | 2 | 0 | 8 | 1 | s2 f0 ✓ |
| string_3_g3.tef | 3 | 0 | 16 | 1 | s3 f0 ✓ |
| string_4_d3.tef | 4 | 0 | 24 | 1 | s4 f0 ✓ |
| string_5_tg4.tef | 5 | 0 | 32 | 1 | s5 f0 ✓ |
| string_1_fret_2.tef | 1 | 2 | 0 | 3 | s1 f2 ✓ |
| string_1_fret_3.tef | 1 | 3 | 0 | 4 | s1 f3 ✓ |

**Large file format (event list, b11 combined encoding):**

For melody notes (b9 = 6, 12, or 18), the encoding is:

```
fret_base = b11 // 64        (upper 2 bits)
remainder = b11 % 64         (lower 6 bits)

if remainder < 32:
    # Strings 1-4: standard encoding
    string = remainder // 8 + 1
    fret = fret_base
else:
    # String 5: extended encoding (banjo short string)
    string = 5
    fret = fret_base + (remainder - 32) // 8

pitch = tuning[string-1] + fret
```

**b9 indicates voice/stem direction, NOT an encoding offset!**

**Decode success: 192/192 melody notes (100%)**

**Example decodings:**
| b11 | Binary | fret_base | remainder | String | Fret | Notes |
|-----|--------|-----------|-----------|--------|------|-------|
| 0   | 00000000 | 0 | 0 | 1 | 0 | s1 open |
| 24  | 00011000 | 0 | 24 | 4 | 0 | s4 open |
| 32  | 00100000 | 0 | 32 | 5 | 0 | s5 open |
| 72  | 01001000 | 1 | 8 | 2 | 1 | s2 fret 1 |
| 160 | 10100000 | 2 | 32 | 5 | 2 | s5 fret 2 |
| 168 | 10101000 | 2 | 40 | 5 | 3 | s5 fret 3 (40-32=8, +1 fret) |

**Known limitations:**
- Accompaniment notes (b9=0) use chord-based encoding (not yet decoded)

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
