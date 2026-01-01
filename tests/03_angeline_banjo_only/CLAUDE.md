# Test 03: Angeline the Baker (Banjo Only)

## Purpose
Isolate banjo notes without guitar track confusion to debug the 65% match rate in test 02.

## Truth Files

Multiple progressively stripped versions created:

| File | Notes | Reading List | Result |
|------|-------|--------------|--------|
| `_no_reading_lists` | 104 | None | **PASS 100%** |
| `_with_reading_list` | 104 | 5 entries (broken) | Needs fix |
| `_with_annotations` | 102 | 5 entries (broken) | Needs fix |

## Key Findings

### 1. Perfect Match Without Reading List
The simplest version (`_no_reading_lists`) achieves **100% pitch match** (104/104 notes).

### 2. New Markers Discovered
- `A` (0x41) - Articulation marker, contains valid note data
- `&` (0x26) - Another articulation marker, contains valid note data
- `C` (0x43) - Chord marker, valid when `decode_string_fret()` succeeds

### 3. Reading List Inconsistency
The reading list in the banjo-only files still references the original 18-measure layout:
- Entry [1]: measures 1-8
- Entry [2]: measures 1-7
- Entry [3]: measures 9-17 (DON'T EXIST)
- Entry [4]: measures 10-16 (DON'T EXIST)
- Entry [5]: measures 18-18 (DOESN'T EXIST)

But banjo-only file only has 8 measures of note data. This causes expansion to fail.

### 4. Annotation Corruption
In annotated files, C-marker notes have chord name data ('FC') in byte 10 instead of fret value, causing decode failure. The stripped version decodes correctly.

## Mike's Ideas

- I added an area of @notes which include some images of the application and observations. I made
  additional sources of tef and midi truth to help you figure out the differences in how data has
  been stored.

## Result

**PARTIAL PASS**
- Basic note parsing: 100% (104/104 on stripped file)
- Reading list expansion: Blocked by inconsistent truth files
- Annotation handling: C-markers corrupted in annotated files

## Next Steps

1. Create a new test file with consistent reading list (e.g., simple A-A-B-B repeat)
2. Or manually edit reading list in TEF to reference only measures 1-8

## Replication

```bash
cd tests/03_angeline_banjo_only
./test
```
