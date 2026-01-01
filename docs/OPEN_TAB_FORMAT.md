# Open Tablature Format (OTF) - Draft Specification

A human-diffable, machine-precise format for storing and rendering tablature and notation for stringed instruments.

## Design Principles

1. **Storage vs Rendering Separation**: The storage format is machine-precise; rendering handles human readability
2. **Tick-based Timing**: Internal timing uses ticks (e.g., 480/beat) that render to any subdivision
3. **Technique Preservation**: Instrument-specific articulations are first-class citizens
4. **Multi-track Support**: Full arrangements with shorthand for backup patterns
5. **Portable**: YAML or JSON serialization, no proprietary extensions

## File Structure

```yaml
otf_version: "1.0"

metadata:
  title: "Foggy Mountain Breakdown"
  composer: "Earl Scruggs"
  arranger: null
  key: "G"
  time_signature: "2/2"  # Cut time (bluegrass standard)
  tempo: 160             # BPM (for playback reference)

timing:
  ticks_per_beat: 480    # High resolution for triplets, swung notes
  # Common subdivisions:
  # - 480 = quarter note
  # - 240 = eighth note
  # - 160 = eighth triplet
  # - 120 = sixteenth note
  # - 80  = sixteenth triplet

tracks:
  - id: "banjo"
    instrument: "5-string-banjo"
    tuning: ["G4", "D3", "G3", "B3", "D4"]  # Open G, 5th string is drone
    capo: 0
    role: "lead"

  - id: "guitar"
    instrument: "6-string-guitar"
    tuning: ["E2", "A2", "D3", "G3", "B3", "E4"]
    capo: 0
    role: "rhythm"
    pattern: "boom-chuck"  # Reference to patterns section

  - id: "bass"
    instrument: "upright-bass"
    tuning: ["E1", "A1", "D2", "G2"]
    role: "rhythm"

# Chord progression for rhythm tracks
progression:
  - measure: 1
    chords: ["G", "G", "G", "G"]  # One chord per beat
  - measure: 2
    chords: ["G", "G", "Em", "Em"]
  # ... or use slash notation:
  # measures: "G / / / | G / Em / | C / / / | D / / / |"

# Named patterns for rhythm instruments
patterns:
  boom-chuck:
    description: "Standard bluegrass guitar backup"
    events:
      - beat: 1
        type: "bass-note"  # Root or fifth
      - beat: 2
        type: "chord-strum"
        mute: true
      - beat: 3
        type: "bass-note"
      - beat: 4
        type: "chord-strum"
        mute: true

# Full notation for lead instruments
notation:
  banjo:
    - measure: 1
      events:
        # Each event has: tick position, string, fret, and optional modifiers
        - tick: 0
          notes:
            - {s: 3, f: 0}           # String 3, fret 0 (open G)
        - tick: 120                  # 16th note later
          notes:
            - {s: 2, f: 0, tech: h}  # Hammer-on
            - {s: 5, f: 0}           # 5th string drone
        - tick: 240
          notes:
            - {s: 2, f: 2, tech: p}  # Pull-off
```

## Timing Model

### Tick Resolution

Using 480 ticks per beat allows clean division for common subdivisions:

| Subdivision | Ticks | Notes per Beat |
|-------------|-------|----------------|
| Quarter     | 480   | 1 |
| Eighth      | 240   | 2 |
| Triplet 8th | 160   | 3 |
| Sixteenth   | 120   | 4 |
| Triplet 16th| 80    | 6 |
| 32nd        | 60    | 8 |

### Meter and Display

The storage format uses absolute ticks. The renderer decides how to display:

- **2/2 (Cut time)**: Common in bluegrass. 4 notes/beat shown as 8ths
- **4/4**: Same 4 notes/beat shown as 16ths
- **3/4 (Waltz)**: 3 beats per measure
- **6/8 (Jig)**: 2 groups of 3 eighth notes

```yaml
time_signature: "2/2"
beat_grouping: [2, 2]  # For 6/8: [3, 3]
```

## Note Representation

### Basic Note Event

```yaml
- tick: 480           # Position in ticks from start of measure
  notes:
    - s: 1            # String number (1 = highest pitch)
      f: 2            # Fret number (0 = open)
      tech: null      # Technique (see below)
      dur: 240        # Duration in ticks (optional, for sustained notes)
```

### String Numbering Convention

Strings are numbered 1-N from highest pitch to lowest:
- **Banjo (5-string)**: 1=D4, 2=B3, 3=G3, 4=D3, 5=G4 (drone)
- **Guitar**: 1=E4, 2=B3, 3=G3, 4=D3, 5=A2, 6=E2
- **Mandolin**: 1=E5, 2=A4, 3=D4, 4=G3 (courses, not individual strings)
- **Bass**: 1=G2, 2=D2, 3=A1, 4=E1

## Instrument-Specific Techniques

### Universal Techniques

| Code | Name | Description |
|------|------|-------------|
| `h` | Hammer-on | Strike string with fretting finger |
| `p` | Pull-off | Pluck string with fretting finger |
| `/` | Slide up | Slide to higher fret |
| `\` | Slide down | Slide to lower fret |
| `b` | Bend | Bend string to raise pitch |
| `r` | Release | Release bend |
| `~` | Vibrato | Oscillate pitch |
| `x` | Mute/Ghost | Muted or ghost note |

### Banjo-Specific

| Code | Name | Description |
|------|------|-------------|
| `choke` | Choke | Dampen string immediately after picking |
| `brush` | Brush | Strum across multiple strings |
| `roll:fwd` | Forward roll | T-I-M picking pattern |
| `roll:bwd` | Backward roll | M-I-T picking pattern |
| `roll:alt` | Alternating roll | T-M-T-I-M-T-I-M |

### Fiddle-Specific

| Code | Name | Description |
|------|------|-------------|
| `bow:d` | Down bow | Bow moves from frog to tip |
| `bow:u` | Up bow | Bow moves from tip to frog |
| `slur` | Slur | Multiple notes in one bow stroke |
| `shuf:nash` | Nashville shuffle | Long-short-short bow pattern |
| `shuf:ga` | Georgia shuffle | Short + 3 slurred notes |
| `chop` | Chop | Percussive muted stroke |
| `dbl` | Double stop | Two strings simultaneously |

### Mandolin-Specific

| Code | Name | Description |
|------|------|-------------|
| `trem` | Tremolo | Rapid alternate picking |
| `chop` | Chop chord | Percussive muted chord on offbeat |
| `dbl` | Double stop | Two courses simultaneously |

### Dobro-Specific

| Code | Name | Description |
|------|------|-------------|
| `bar` | Bar slide | Slide with tone bar |
| `vib:bar` | Bar vibrato | Vibrato using bar movement |
| `pull` | Pull-off | To open string only |

### Guitar-Specific

| Code | Name | Description |
|------|------|-------------|
| `pick:d` | Downstroke | Pick moving down |
| `pick:u` | Upstroke | Pick moving up |
| `rest` | Rest stroke | Pick rests on adjacent string |
| `cross` | Crosspick | Roll pattern across strings |

### Bass-Specific

| Code | Name | Description |
|------|------|-------------|
| `slap` | Slap | Strike string with thumb |
| `pop` | Pop | Pull string and release |
| `snap` | Snap | Aggressive pizzicato (Bartok) |
| `trip` | Triplet slap | Snap + 2 fingerboard hits |

## Duration and Ties

For notes that need explicit duration (tremolo, sustained notes):

```yaml
- tick: 0
  notes:
    - {s: 1, f: 5, dur: 1920, tech: trem}  # Whole note tremolo
```

For tied notes across bar lines, use `tie: start` and `tie: end`:

```yaml
# End of measure 1
- tick: 1440
  notes:
    - {s: 1, f: 5, tie: start}

# Start of measure 2
- tick: 0
  notes:
    - {s: 1, f: 5, tie: end}
```

## Chord Symbols and Progressions

### Chord Representation

```yaml
chords:
  G:
    type: "major"
    bass: "G"
    voicing: [{s: 6, f: 3}, {s: 5, f: 2}, {s: 4, f: 0}, {s: 3, f: 0}, {s: 2, f: 0}, {s: 1, f: 3}]

  Em:
    type: "minor"
    bass: "E"
```

### Slash Notation for Rhythm

```yaml
progression:
  - measures: "| G / / / | C / G / | D / / / | G / / / |"
    repeats: 2
```

## Sections and Structure

```yaml
structure:
  - name: "A Part"
    measures: [1, 8]
    repeats: 2

  - name: "B Part"
    measures: [9, 16]
    repeats: 2

# Reading list for playback order
reading_list:
  - section: "A Part"
    times: 2
  - section: "B Part"
    times: 2
  - section: "A Part"
    times: 1
    ending: "tag"  # Special ending variation
```

## Rendering Hints

The storage format can include optional hints for renderers:

```yaml
render_hints:
  prefer_tab: true           # Show tablature by default
  prefer_notation: false     # Show standard notation
  show_chord_diagrams: true  # Include chord diagrams
  condensed_repeats: true    # Use repeat signs vs writing out
```

## File Extensions and MIME Types

- **Extension**: `.otf.yaml` or `.otf.json`
- **MIME type**: `application/vnd.otf+yaml` or `application/vnd.otf+json`

## Compatibility Notes

### Import From
- **TEF (TablEdit)**: Via tef-parser, maps to OTF structure
- **ABC Notation**: Parse and convert time/note structure
- **MusicXML**: Full notation import (tab positions need inference)
- **Guitar Pro**: Via TuxGuitar or alphaTab libraries

### Export To
- **ABC Notation**: For sharing, folk tune databases
- **MIDI**: For audio playback (loses tab-specific info)
- **MusicXML**: For notation software interchange
- **HTML/SVG**: For web rendering (via alphaTab, VexFlow, or custom)

## Example: Simple Banjo Lick

```yaml
otf_version: "1.0"

metadata:
  title: "G Lick"
  key: "G"
  time_signature: "2/2"
  tempo: 160

timing:
  ticks_per_beat: 480

tracks:
  - id: "banjo"
    instrument: "5-string-banjo"
    tuning: ["D4", "B3", "G3", "D3", "G4"]
    role: "lead"

notation:
  banjo:
    - measure: 1
      events:
        - tick: 0
          notes: [{s: 3, f: 0}]           # Open G
        - tick: 120
          notes: [{s: 2, f: 0}]           # Open B
        - tick: 240
          notes: [{s: 1, f: 0}, {s: 5, f: 0}]  # Open D + 5th string
        - tick: 360
          notes: [{s: 2, f: 0}]
        - tick: 480
          notes: [{s: 3, f: 0, tech: h}]  # Hammer prep
        - tick: 600
          notes: [{s: 3, f: 2}]           # Hammer to A
        - tick: 720
          notes: [{s: 2, f: 0}, {s: 5, f: 0}]
        - tick: 840
          notes: [{s: 1, f: 0}]
```

---

## Open Questions

1. **Swing/Feel**: How to represent swing timing? Percentage offset or named feel?
2. **Dynamics**: Include velocity/loudness? (mf, f, ff, accents)
3. **Lyrics**: Align lyrics with notes for vocal parts?
4. **Fingering**: Left-hand finger numbers for classical/complex passages?
5. **Right-hand patterns**: Notate which finger (T/I/M for banjo) picks each note?

## Versioning and Extensibility

### Semantic Versioning

OTF uses semantic versioning: `MAJOR.MINOR`

- **MAJOR**: Breaking changes (parsers for v1.x cannot read v2.x)
- **MINOR**: Additive changes (v1.0 parsers can read v1.1 files, ignoring unknown fields)

### Forward Compatibility Rules

1. **Unknown fields MUST be preserved**: Parsers MUST NOT discard fields they don't recognize
2. **New technique codes**: Added in MINOR versions; old parsers treat as `null`
3. **New instrument types**: Added in MINOR versions; old parsers use string as-is
4. **Structural changes**: Require MAJOR version bump

### Extension Namespaces

Custom extensions use prefixed keys to avoid conflicts:

```yaml
# Vendor extension example
x-tabledit:
  original_file: "song.tef"
  export_date: "2025-01-15"

# Community extension
x-banjohangout:
  tune_id: 12345
```

### Deprecation Policy

Deprecated features are marked in the spec and remain valid for 2 MAJOR versions:

```yaml
# Deprecated in v1.1, removed in v3.0
deprecated:
  - field: "old_timing_format"
    replaced_by: "timing.ticks_per_beat"
    removed_in: "3.0"
```

### Minimum Parser Requirements

A conforming v1.x parser MUST:
1. Parse `otf_version` and reject files with incompatible MAJOR version
2. Preserve unknown fields during read/write cycles
3. Support all technique codes defined in this spec (treat unknown as `null`)
4. Handle missing optional fields with documented defaults

## Version History

- **v1.0 (Draft)**: Initial specification
  - Core note representation with string/fret/technique
  - Multi-track support with roles
  - Tick-based timing (480 ticks/beat)
  - Instrument-specific technique codes
  - Reading list for repeats
