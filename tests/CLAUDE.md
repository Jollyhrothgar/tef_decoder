# TEF Parser Test Suite

Structured tests for validating the TEF parser against TablEdit's own exports.

## Test Matrix

| Test | Status | Match Rate | Key Learning |
|------|--------|------------|--------------|
| 01_multi_note_simple | PASS | 100% | Basic format works, no reading list needed |
| 02_angeline_banjo_guitar | PARTIAL | 65% (123/188 banjo) | Reading list expansion works, but missing notes |
| 03_angeline_banjo_only | PASS | 100% (no RL) | Basic parsing works! New markers A, &, C discovered |
| 04_simple_repeat_aabb | PENDING | - | Need to verify reading list expansion math |
| 05_chord_voicing | PENDING | - | Need to understand C-marker and chord encoding |
| 06_one_note_per_measure | PENDING | - | Need to verify measure boundary calculations |

## How Tests Work

Each test has:
- `truth/input.tef` - Original TablEdit file
- `truth/expected.mid` - TablEdit's MIDI export (source of truth)
- `truth/*.abc`, `*.ly` - Other TablEdit exports if available
- `parsed/output.mid` - Our parser's MIDI output
- `CLAUDE.md` - Purpose, results, learnings
- `test` - Executable script that runs comparison

Run a test:
```bash
cd tests/01_multi_note_simple && ./test
```

Run all tests:
```bash
./tests/fixtures/run_all
```

## Open Questions

### 1. What does byte 8 (b8) represent?
- In simple files: b8=0 is primary melody, b8=1 is secondary
- In multi-instrument files: b8 has values 0-3, meaning unclear
- Hypothesis: voice/part number within arrangement, not instrument

### 2. Reading list offset varies
- angeline: 0x4a0
- shuck_the_corn: 0x5a6
- Now using pattern search instead of fixed offset

### 3. Some records have marker bytes in wrong position
- `b10=0x46='F'` instead of fret value
- Possibly chord name data embedded in record?

### 4. Missing pitches
- angeline's MIDI has pitch 53 (F3), can't find source in TEF
- Either different encoding or in C-marker records we skip

## Key Findings

### Reading List Structure (offset varies, 32 bytes/entry)
```
Byte 0: 0x00
Byte 1: from_measure (1-indexed)
Byte 2: 0x00
Byte 3: to_measure (1-indexed)
Bytes 4-31: reserved/padding
```

### Note Record Structure (12 bytes)
```
Bytes 0-5:  Flags/articulation
Byte 6:     Position low + string encoding (bits 3-5)
Byte 7:     Position high
Byte 8:     Voice/part indicator (meaning varies by file)
Byte 9:     Reserved
Byte 10:    Fret + 1
Byte 11:    Marker (I/F/L/C/@)
```

### Timing Scales
| File Type | Ticks/Beat | Ticks/Measure (4/4) | MIDI Scale |
|-----------|------------|---------------------|------------|
| High-res (angeline) | 1408 | 5632 | 0.1705 |
| Medium (shuck) | 960 | 3840 | 0.125 |
| Low (Multi Note) | 320 | 1280 | 0.375 |

## Tests Awaiting Truth Files

Tests 03-06 have been set up with test scripts and documentation.
**Action Required**: Create truth files (input.tef + expected.mid) in TablEdit.

See each test's `CLAUDE.md` for creation instructions:
- `tests/03_angeline_banjo_only/CLAUDE.md` - Delete guitar from angeline
- `tests/04_simple_repeat_aabb/CLAUDE.md` - 4 measures with A-A-B-B reading list
- `tests/05_chord_voicing/CLAUDE.md` - Single chord to understand C-marker
- `tests/06_one_note_per_measure/CLAUDE.md` - 4 measures, 1 note each at beat 1

---

### Specific Investigation: Position 16 Divergence

In test 02 (angeline), first mismatch is at note index 16:
- Expected: pitch 53 at MIDI time 2880
- Got: pitch 69 at MIDI time 3360

**Question for TablEdit UI**:
- What note plays at measure 3, beat 1 in angeline?
- Is pitch 53 (F3 = string 4, fret 3) visible in the tablature there?
