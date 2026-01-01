# Human Tab Format (HTF) - Draft

A human-writable text format for bluegrass/acoustic tablature.

## Design Goals

1. **Readable as-is** - no tooling needed to understand it
2. **Fast to type** - minimal syntax, common case is clean
3. **Preserves timing and techniques** - full musical precision
4. **Easy to render** - parses to internal structure for viewer/playback
5. **WYSIWYG-friendly** - serves as save format for visual editors

## Role in the Ecosystem

```
WYSIWYG Editor ──saves──► HTF (source of truth, human-readable)
                            │
                         parse
                            ▼
                    [internal structure]
                       │         │
                    render    synthesize
                       ▼         ▼
                     SVG       MIDI/Audio
```

**HTF** is the primary file format - what you author, save, share, and version control.

**OTF** (Open Tab Format) remains useful for:
- Computational comparison of variations
- Archival precision
- Tracking branching variations of tunes (e.g., "Earl's break" vs "JD's break")

Most users will use a WYSIWYG editor; HTF is what it saves to disk.

## Basic Structure

```
# Title
instrument tuning | tempo BPM | meter | L:default-length

section: | notes... | notes... |

play: section order
```

## Example

```
# Foggy Mountain Breakdown
banjo openG | tempo 160 | 2/2 | L:1/8

A: |: 3.0 2.0 1.0+5.0 2.0 | 3.0 3h2 2.0 1.0 :|
B: |: 2.0 1/2 1.0 2.0 | 2.0 3.0 2p0 1.0 :|

play: AABB A(tag)
```

## Note Syntax

### Basic notes
- `3.0` - string 3, fret 0
- `1.12` - string 1, fret 12
- `1.0+5.0` - chord (multiple strings simultaneous)

### Techniques
- `3h2` - hammer-on to fret 2 on string 3
- `3p0` - pull-off to open on string 3
- `1/5` - slide up to fret 5 on string 1
- `1\3` - slide down to fret 3 on string 1
- `2~` - vibrato
- `2x` - muted/ghost note

### Duration

Default note length set by `L:` header (ABC-style):
- `L:1/8` - default is eighth note
- `L:1/16` - default is sixteenth note
- `L:1/4` - default is quarter note

Modifiers for individual notes:
- `3.0` - default length
- `3.0*` - double (or `3.0*2`)
- `3.0/` - half (or `3.0/2`)
- `3.0*3/2` - dotted (1.5x)

### Groupings
- `[1.0 2.0 3.0]` - chord (all notes at once)
- `(3.0 3h2)` - 16th note pair in space of 8th
- `{3.0 2.0 1.0}` - triplet

## Time Signatures

```
| 4/4    - common time (4 quarter notes per measure)
| 2/2    - cut time (2 half notes per measure)
| 3/4    - waltz time (3 quarter notes per measure)
| 6/8    - jig time (2 groups of 3 eighths)
```

With `L:1/8` default:
- 4/4 = 8 eighth notes per measure
- 2/2 = 8 eighth notes per measure
- 3/4 = 6 eighth notes per measure
- 6/8 = 6 eighth notes per measure

## Measures and Repeats

- `|` - bar line
- `|:` - repeat start
- `:|` - repeat end
- `|1` - first ending
- `|2` - second ending

## Sections and Structure

```
A: | ... |
B: | ... |
tag: | ... |

play: AABB A tag
```

## Multi-track

```
# Foggy Mountain Breakdown

== banjo openG | lead
A: |: 3.0 2.0 1.0+5.0 2.0 | 3.0 3h2 2.0 1.0 :|

== guitar standard | rhythm
A: |: [6.3 4.0 3.0] [4.0 3.0 2.0] | ... :|

== bass standard
A: |: 4.G 4.G | 3.D 3.D :|

play: AABB
```

## Standard Tunings

```
banjo openG     -> G4 D3 G3 B3 D4  (5-string, 5th string is drone)
banjo openD     -> F#4 D3 F#3 A3 D4
guitar standard -> E2 A2 D3 G3 B3 E4
guitar dropD    -> D2 A2 D3 G3 B3 E4
mandolin standard -> G3 D4 A4 E5
bass standard   -> E1 A1 D2 G2
dobro openG     -> G2 B2 D3 G3 B3 D4
fiddle standard -> G3 D4 A4 E5
```

## Open Syntax Questions

1. **Note separator** - Current `3.0` requires many periods. Alternatives:
   - `3-0` (dash) - cleaner, unambiguous
   - `30` (none) - ambiguous for fret 10+
   - `3:0` (colon) - conflicts with section labels?

2. **Pitch vs fret for bass/fiddle** - Bass players think in pitch. Support `4.G` as "G on string 4"? Compiler resolves to fret.

3. **Chord shorthand** - For rhythm tracks only. Lead tracks spell out every note.
   ```
   == guitar standard | rhythm
   A: | G / / / | C / G / |

   == banjo openG | lead
   A: | 3.0 2.0 1.0+5.0 2.0 |
   ```

4. **Lyrics** - Parallel line syntax:
   ```
   A: | 3.0 2.0 1.0 2.0 |
   W: | Roll-ing in my |
   ```

5. **Right-hand patterns** - Probably overkill to notate T/I/M explicitly. Banjo players know fingering from the roll pattern. Maybe for teaching materials only.

6. **Roll/lick abstractions** - Future feature. Could define pattern libraries:
   ```
   import: scruggs-licks
   A: | @fwd-G | @fwd-C |
   ```
   But this is v2 thinking - keep v1 explicit.

## Bluegrass Edge Cases (from Gemini feedback)

1. **Pickup notes** - Songs often start on beat 4, not beat 1. Allow partial opening measure.

2. **Capo** - Store relative fret (what finger does). Capo position in metadata. Renderer calculates pitch.

3. **Slide types** - Instant (shift) vs continuous (legato). May need `shift:` vs `/` syntax.

4. **Scruggs tuners** - Mid-song retuning. Needs tuning change event.

5. **5th string rendering** - String 5 is physically "above" string 4 but high pitch. Renderer must handle this.

6. **Swing feel** - Keep ticks straight in storage, add `feel: swing` to metadata. Playback engine adjusts.

## Parsing

HTF parses to an internal structure (documented in OTF spec) for:
- Rendering in viewer
- Audio playback
- Export to other formats (MIDI, MusicXML, ABC)
- Computational comparison of tune variations
