# Bluegrass Tablature Tools

An open ecosystem for bluegrass/acoustic tablature: preservation, playback, and authoring.

## Project Evolution

**Phase 1: Preservation (working)**
- Reverse-engineered TablEdit `.tef` format (v2 and v3)
- Parser extracts notes, timing, techniques, multi-track arrangements
- TODO: more technique types, grace notes, chord diagrams

**Phase 2: Interchange Format (working)**
- OTF (Open Tab Format) - machine-readable JSON/YAML
- Precise timing, techniques, reading lists, multi-track support
- TODO: lyrics, chord symbols, ornaments, dynamics

**Phase 3: Viewer & Playback (working)**
- Web-based SVG tablature renderer with basic beaming
- WebAudioFont integration for instrument sounds
- Multi-track playback with mixer controls
- TODO: print/PDF, transposition, chord diagrams, lyrics display,
  mobile layout, keyboard nav, standard notation option

**Phase 4: Authoring (draft)**
- HTF (Human Tab Format) - text-based authoring format
- Compiles to OTF for rendering/playback
- See `docs/HUMAN_TAB_FORMAT.md` for draft spec

## Quick Start

```bash
uv tool install .         # Install CLI globally
tef parse sample.tef      # Parse and show structure
tef midi sample.tef       # Export to MIDI
uv run pytest             # Run tests
```

## Project Structure

```
TablEdit_Reverse/
├── CLAUDE.md                 # This file
├── samples/                  # Sample .tef files organized by type
│   ├── single_note/          # Single note test files
│   ├── multi_note/           # Multi-note test files
│   └── songs/                # Complete song files (v2 and v3)
├── src/tef_parser/           # Core parser
│   ├── __init__.py
│   ├── reader.py             # TEFReader class (v2 + v3 support)
│   ├── cli.py                # CLI entry point
│   └── otf.py                # OTF format exporter
├── viewer/                   # Web-based viewer/player
│   └── index.html            # SVG tab renderer + WebAudioFont playback
├── tests/
│   ├── test_parser.py        # Unit tests
│   └── 01-03_*/              # Integration test fixtures
└── docs/
    ├── OPEN_TAB_FORMAT.md    # OTF specification (machine format)
    └── HUMAN_TAB_FORMAT.md   # HTF draft spec (authoring format)
```

## Format Support

| Version | Files | Status |
|---------|-------|--------|
| **V2** (pre-3.00) | `mandolin_foggy_mountain_breakdown.tef` | Working |
| **V3** (3.00+) | `shuck_the_corn.tef`, `angeline_the_baker.tef` | Working |

The parser auto-detects version and uses the appropriate decoder.

## CLI Commands

```bash
# Parse and show file structure
tef parse samples/songs/shuck_the_corn.tef

# Export to OTF (Open Tab Format) - YAML
tef otf samples/songs/shuck_the_corn.tef output.otf.yaml

# Export to OTF - JSON
tef otf samples/songs/shuck_the_corn.tef --json output.otf.json

# Export to MIDI (single track)
tef midi samples/songs/shuck_the_corn.tef output.mid

# Export specific track (0=first instrument)
tef midi -t 0 input.tef output.mid

# List tracks without exporting
tef midi -l input.tef

# Show file version
tef version input.tef

# View as ASCII timeline
tef view input.tef
```

For development without global install: `uv run tef <command>`

## Format Stack

```
WYSIWYG Editor / Power User
         ↓ saves
HTF (Human Tab Format)     <- Source of truth (text-based, diffable)
         ↓ parses to
[Internal Structure]       <- What OTF spec documents
         ↓ renders to
SVG + Audio                <- Viewer with WebAudioFont playback
```

**HTF** = primary file format (authoring, saving, version control)
**OTF** = internal data model + archival format for variation tracking

**TEF → HTF**: Preservation path (import legacy arrangements)
**Editor → HTF**: Authoring path (WYSIWYG saves to HTF)

## Viewer

Open `viewer/index.html` in a browser, load an `.otf.json` or `.otf.yaml` file.

Features:
- SVG tablature rendering with proper beaming
- WebAudioFont playback (banjo, guitar, mandolin, bass, fiddle, dobro)
- Multi-track "Play All" with mixer controls (volume, sustain, decay)
- Loop mode for practice
- Tempo adjustment

## OTF (Open Tab Format)

See `docs/OPEN_TAB_FORMAT.md` for full specification.

Key features:
- **Human-diffable**: YAML or JSON, clean structure
- **Multi-track**: Full arrangements with lead and rhythm roles
- **Tick-based timing**: 480 ticks/beat for precise subdivisions
- **Technique codes**: `h` (hammer-on), `p` (pull-off), `/` (slide), etc.
- **Reading list**: Preserves repeat structure for playback
- **Extensible**: x-prefixed namespaces for custom extensions

## HTF (Human Tab Format)

See `docs/HUMAN_TAB_FORMAT.md` for draft specification.

Design goals:
- Readable without tooling
- Fast to type (minimal syntax)
- Compiles to OTF for rendering/playback

Example:
```
# Cripple Creek
banjo openG | tempo 160 | 2/2 | L:1/8

A: |: 3.0 2.0 1.0+5.0 2.0 | 3.0 3h2 2.0 1.0 :|

play: AA
```

## TEF Format Summary

### V3 Format (3.00+)

**Header**: 256 bytes binary, starts with format_id `0x0010`
- `debt` marker at offset 56 points to component section
- Reading list pointer at offset 128

**Components**: 12-byte records
```
Bytes 0-3:  Location (encodes measure + position + string)
Byte 4:     Component type (notes have fret in bits 0-4)
Byte 5:     Marker (I=Initial, F=Fret, L=Legato)
Bytes 6-11: Component-specific data
```

**Location decoding** (TuxGuitar format):
```python
total_strings = sum(track.num_strings for track in tracks)
VALUE_PER_POSITION = 32 * total_strings
cumulative_string = (location % VALUE_PER_POSITION) // 8
position = location // VALUE_PER_POSITION  # 16th note grid
```

### V2 Format (pre-3.00)

**Header**: ASCII strings at start (title, composer, comments), then fixed offsets
- Bytes 0-199: Info section (null-terminated strings)
- Byte 200-201: Measures count
- Byte 202/204: Time signature (num/denom)
- Byte 220-221: Tempo
- Byte 240: Total strings
- Byte 256-257: Component count
- Byte 258+: Components

**Components**: 6-byte records
```
Bytes 0-1:  Location
Byte 2:     Type+fret (bits 0-4 = fret+1)
Byte 3:     Duration
Bytes 4-5:  Effects
```

**Location decoding**:
```python
ts_size = (256 * time_num) // time_denom  # 256 for 4/4
position = location % ts_size
string = (location // ts_size) % num_strings
measure = location // (ts_size * num_strings)
```

### Common Formulas

**Tuning bytes to MIDI pitch**:
```python
midi_pitch = 96 - tuning_byte
```

**Standard tunings** (MIDI pitches, high to low string):
- Open G Banjo: [62, 59, 55, 50, 67] (D4, B3, G3, D3, G4)
- Standard Guitar: [64, 59, 55, 50, 45, 40] (E4, B3, G3, D3, A2, E2)
- Mandolin GDAE: [76, 69, 62, 55] (E5, A4, D4, G3)
- Bass: [43, 38, 33, 28] (G2, D2, A1, E1)

## Test Files

### Key Reference Files
| File | Version | Tracks | Notes |
|------|---------|--------|-------|
| `shuck_the_corn.tef` | 3.05 | Banjo, Guitar, Bass | Primary v3 test, has reading list |
| `angeline_the_baker...tef` | 3.05 | Banjo, Guitar | Spiked 5th string, reading list |
| `mandolin_foggy_mountain_breakdown.tef` | 2.00 | Mandolin, Guitar, Bass | Primary v2 test |

### Test Results
```
shuck_the_corn:     214 banjo notes → 397 expanded (reading list)
angeline_the_baker: 104 banjo notes → 188 expanded (reading list)
mandolin_foggy:     288 notes (133 mandolin, 124 guitar, 31 bass)
```

## Development

```bash
# Run tests
uv run pytest -v

# Test specific file
uv run python3 -c "
from tef_parser import TEFReader
tef = TEFReader('samples/songs/shuck_the_corn.tef').parse()
print(tef.dump())
"
```

## TuxGuitar Reference

The parser is based on TuxGuitar's TEF implementation:
- V3: `tuxguitar/desktop/TuxGuitar-tef/src/app/tuxguitar/io/tef3/`
- V2: `tuxguitar/desktop/TuxGuitar-tef/src/app/tuxguitar/io/tef2/`

Key files: `TEInputStream.java`, `TESongParser.java`
