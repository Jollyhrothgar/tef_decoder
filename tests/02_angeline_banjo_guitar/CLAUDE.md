# Test 02: Angeline the Baker (Banjo + Guitar)

## Purpose
Test complex multi-track file with reading list (repeat structure).

## Source File
- **Original**: `angeline_the_baker_banjo_guitar_banjo_fifth_string_tuned_1_step_higher.tef`
- **Title**: "in D with no capo - 5th spiked to A"
- **Created in**: TablEdit 3.05

## Structure
- Two instruments: Banjo Open G (5th spiked to A), Guitar Standard
- Spiked tuning: [62, 59, 55, 50, 69] (5th string = A4 instead of G4)
- Reading list with 5 entries (repeat structure)
- Timing: 1408 ticks/beat (high resolution)

### Reading List
```
[01] measures 1-8    # A part
[02] measures 1-7    # A part repeat (first ending)
[03] measures 9-17   # B part
[04] measures 10-16  # B part variation
[05] measures 18-18  # Ending
Total: 32 playback measures
```

### MIDI Track Breakdown
| Track | Instrument | Notes |
|-------|------------|-------|
| 1 | Banjo open G | 188 |
| 2 | Guitar Standard | 297 |

## Result
**PARTIAL - 65% match (banjo track only)**

```
Source notes:  67 (b8=0 filter)
Expanded:      123 (via reading list)
Expected:      188 (banjo track)
First 16:      100% match
Overall:       ~65% match
```

## Issues Found

### 1. Missing notes after position 16
First 16 notes match perfectly, then divergence. At MIDI time 2880:
- Expected: pitches 59, 53
- Got: pitch 69 (wrong timing)

### 2. C-marker notes excluded
Position 16896 has C-marker notes with b8=0 that we filter out:
```
TEF 16896: C s2f0 pitch=59 b8=0  ← Should this be included?
```

### 3. Missing pitch 53
Original MIDI has 4 instances of pitch 53 (F3 = string 4, fret 3).
Cannot find any TEF note that produces this pitch.

### 4. Decode failures
Some records have `b10=0x46='F'` (marker in fret position):
```
Raw: 00 00 00 00 00 00 18 42 00 00 46 43
                             ^'F' ^'C'
```

## Key Bytes

Reading list at offset 0x4a0:
```
0x4a0: 00 01 00 08  → measures 1-8
0x4c0: 00 01 00 07  → measures 1-7
0x4e0: 00 09 00 11  → measures 9-17
0x500: 00 0a 00 10  → measures 10-16
0x520: 00 12 00 12  → measures 18-18
```

## Learnings

1. **Reading list expansion works** - 67 notes → 123 expanded
2. **b8=0 filter is correct** for this file (67 vs 31 notes)
3. **Some notes missing** - either in C markers or decode failures
4. **Guitar track not extracted** - we only target banjo melody

## What Would Help

1. Banjo-only export of this file (remove guitar track in TablEdit)
2. Check TablEdit UI: what does Reading List show?
3. What notes play at measure 3 beat 1? (where we diverge)

## Replication

```bash
cd tests/02_angeline_banjo_guitar
./test
```
