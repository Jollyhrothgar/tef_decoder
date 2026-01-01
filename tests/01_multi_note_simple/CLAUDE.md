# Test 01: Multi Note Simple

## Purpose
Validate basic note parsing without complex features (no reading list, single track).

## Source File
- **Original**: `Multi Note.tef` (renamed to `input.tef`)
- **Title**: "Blue Ridge Cabin Home"
- **Created in**: TablEdit 3.05

## Structure
- Single instrument: Banjo Open G
- 36 melody notes
- No reading list (straight playback)
- No repeats
- Timing: 320 ticks/beat (low resolution)

## Result
**PASS - 100% pitch match**

```
Original MIDI: 36 notes
Parsed MIDI:   36 notes
Pitch matches: 36/36 (100%)
```

## Key Bytes

Note region starts after `debt` marker. Sample record:
```
Offset  Hex                         Decoded
------  --------------------------  -------
0x648   00 00 00 01 00 00 00 42...  Position 0, string 1, fret 0, marker 'B'
```

## Learnings

1. **No reading list needed** - Simple files play straight through
2. **b8=0 filter works** - All melody notes have b8=0
3. **Timing scale**: TEF 320 ticks → MIDI 120 ticks (scale 0.375)
4. **String encoding confirmed**: `(byte6 & 0x38) >> 3` maps to strings 1-5

## Replication

```bash
cd tests/01_multi_note_simple
./test
```
