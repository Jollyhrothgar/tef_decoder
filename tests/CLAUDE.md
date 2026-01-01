# TEF Parser Test Suite

## Unit Tests

Run with: `uv run pytest -v`

| Test | Description |
|------|-------------|
| `test_read_header` | V3 header parsing (version, format_id) |
| `test_parse_title` | Title extraction |
| `test_parse_sections` | Section markers (A Part, B Part) |
| `test_parse_instruments` | Instrument detection with string counts |
| `test_parse_chords` | Chord symbol extraction |
| `test_tuning_intervals` | Tuning interval validation |
| `test_parse_note_events` | Note event extraction |
| `test_note_event_structure` | Record structure validation |
| `test_v2_file_parsing` | V2 format support |

## Integration Tests

Located in `tests/01-03_*/` directories.

| Test | File | Status |
|------|------|--------|
| 01_multi_note_simple | Multi Note.tef | 100% match |
| 02_angeline_banjo_guitar | angeline...tef | 65% (reading list) |
| 03_angeline_banjo_only | angeline (banjo only) | 100% match |

Run: `./tests/fixtures/run_all`

## Test Structure

Each integration test has:
```
tests/XX_name/
├── CLAUDE.md           # Test documentation
├── test                # Executable test script
├── truth/
│   ├── input.tef       # Source TEF file
│   └── expected.mid    # TablEdit's MIDI export
└── parsed/
    └── output.mid      # Our parser's output
```
