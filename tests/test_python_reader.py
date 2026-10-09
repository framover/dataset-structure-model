"""
The Python reference reader: passes every conformance case, and its pieces
behave as the extraction and listing contracts say.
"""
import json

import pytest

from conftest import CONFORMANCE_DIR, REPO_ROOT, minimal_config
from dsm import (Config, ConfigError, ExtractorRegistry, Listing, compare_results, listing, load_config,
                 validate_config, walk)
from dsm.cli import main
from dsm.conformance import FIXTURE_EXTRACTORS, run_case, run_cases
from dsm.config import format_token
from dsm.extract import apply_slice, ldml_to_strftime, normalize, parse_temporal
from dsm.listing import listing_from_dict, root_from_lines


# --------------------------------------------------------------------------- conformance

def pytest_generate_tests(metafunc):
    if "case_dir" in metafunc.fixturenames:
        dirs = sorted(p for p in CONFORMANCE_DIR.iterdir() if p.is_dir())
        metafunc.parametrize("case_dir", dirs, ids=[d.name for d in dirs])


def test_reader_passes_conformance_case(case_dir):
    result = run_case(case_dir, ExtractorRegistry(FIXTURE_EXTRACTORS))
    assert result.status == "pass", f"{case_dir.name}:\n  " + "\n  ".join(result.diffs)


def test_unregistered_extractor_skips_case_and_flags_records():
    case = CONFORMANCE_DIR / "function-extractor"
    assert run_case(case, ExtractorRegistry()).status == "skip"
    config = load_config(case / "config.json")
    with (case / "listing.json").open() as f:
        result = walk(config, listing_from_dict(json.load(f)), ExtractorRegistry())
    assert result.unresolved_extractors == {"session_number_from_folder_name"}
    sessions = [r for r in result.records if r.entity_type == "session"]
    assert sessions and all(any(i.code == "unresolved-extractor" for i in r.issues) for r in sessions)
    assert all("session_number" not in r.metadata for r in sessions)


# --------------------------------------------------------------------------- extraction contract

@pytest.mark.parametrize("spec,expected", [("0:4", "m110"), ("5:13", "20250510"), (":-4", "m110-20250510-001_raw"),
                                           (":", "m110-20250510-001_raw.tif"), ("-3:", "tif"), ("9:", "0510-001_raw.tif")])
def test_slices_are_python_slices(spec, expected):
    assert apply_slice("m110-20250510-001_raw.tif", spec) == expected


@pytest.mark.parametrize("fmt,text,data_type,expected", [
    ("yyyyMMdd", "20250523", "date", "2025-05-23"),
    ("yyyy_MM_dd", "2025_05_23", "date", "2025-05-23"),
    ("HH_mm_ss", "10_00_00", "time", "10:00:00"),
    ("yyyy-MM-dd'T'HHmmss", "2025-05-23T100000", "datetime", "2025-05-23T10:00:00"),
    ("yyMMdd", "170518", "date", "2017-05-18"),
    # two-digit years fall in 1969-2068, the strptime window; the MATLAB reader pins the same pivot
    ("yyMMdd", "690518", "date", "1969-05-18"),
    ("yyMMdd", "680518", "date", "2068-05-18"),
])
def test_ldml_formats_parse_to_iso(fmt, text, data_type, expected):
    assert parse_temporal(text, fmt, data_type) == expected


def test_ldml_translation():
    assert ldml_to_strftime("yyyy-MM-dd'T'HH:mm:ss") == "%Y-%m-%dT%H:%M:%S"
    assert ldml_to_strftime("yyMMdd") == "%y%m%d"
    assert ldml_to_strftime("yyyyyy") == "%Y%y"  # the longer token is matched first


def test_normalize_modes():
    assert normalize("sub-m110", {"normalize": "strip_prefix", "normalizePattern": "sub-"}) == "m110"
    assert normalize("m110.raw", {"normalize": "strip_suffix", "normalizePattern": ".raw"}) == "m110"
    assert normalize("  AB ", {"normalize": "trim"}) == "AB"
    assert normalize("AB", {"normalize": "lowercase"}) == "ab"
    assert normalize("ab", {}) == "ab"


# --------------------------------------------------------------------------- listings

def test_root_from_find_output_infers_directories():
    root = root_from_lines("raw", "main", ["./m110/20250523_baseline/movie.tif", "m110/notes.txt", "", "# comment", "empty/"])
    assert root.entries == ["empty/", "m110/", "m110/20250523_baseline/", "m110/20250523_baseline/movie.tif", "m110/notes.txt"]


def test_listing_adds_missing_ancestors_and_rejects_bad_paths():
    doc = {"roots": [{"dataLocationIdentifier": "raw", "rootStoragePathIdentifier": "main", "entries": ["a/b/c.txt"]}]}
    assert listing_from_dict(doc).roots[0].entries == ["a/", "a/b/", "a/b/c.txt"]
    from dsm import ListingError
    with pytest.raises(ListingError):
        listing_from_dict({"roots": [{"dataLocationIdentifier": "raw", "rootStoragePathIdentifier": "main", "entries": ["../x"]}]})


def test_walk_real_directory(tmp_path):
    (tmp_path / "m110" / "20250523_baseline").mkdir(parents=True)
    (tmp_path / "m110" / "20250523_baseline" / "movie.tif").write_bytes(b"")
    (tmp_path / "temp").mkdir()
    root = listing.root_from_directory("raw", "main", tmp_path)
    config = Config(minimal_config())
    result = walk(config, Listing([root]))
    assert [r.entity_type for r in result.records] == ["subject", "session"]
    assert result.records[1].metadata == {"subject_id": "m110", "session_id": "baseline"}
    assert [u.path for u in result.unmatched] == ["temp/"]


# --------------------------------------------------------------------------- validation

def test_validate_config_reports_codes():
    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["rootStoragePaths"][0]["isAvailable"] = True
    with pytest.raises(ConfigError) as e:
        validate_config(doc)
    assert e.value.code == "schema-validation"
    doc = minimal_config()
    doc["entityTypes"][0]["identifierRef"] = "missing"
    with pytest.raises(ConfigError) as e:
        validate_config(doc)
    assert e.value.code == "reference-integrity"


def test_draft_blocks_are_rejected_unless_allowed():
    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["metadataMapping"].append(
        {"metadataRef": "session_id", "extraction": {"method": "sidecar", "filePattern": "*.json", "contentPath": "id"}})
    with pytest.raises(ConfigError) as e:
        validate_config(doc)
    assert e.value.code == "unsupported-draft"
    validate_config(doc, reject_draft=False)


def test_local_overlay_supplies_preferences(tmp_path):
    doc = minimal_config()
    (tmp_path / "ds.json").write_text(json.dumps(doc))
    (tmp_path / "ds.local.json").write_text(json.dumps({"preferences": {"defaultDataLocationIdentifier": "raw"}}))
    assert load_config(tmp_path / "ds.json").preferences == {"defaultDataLocationIdentifier": "raw"}


# --------------------------------------------------------------------------- comparison rules

def test_compare_is_order_and_message_insensitive():
    with (CONFORMANCE_DIR / "folder-hierarchy-basic" / "expected.json").open() as f:
        expected = json.load(f)
    actual = json.loads(json.dumps(expected))
    actual["records"].reverse()
    for record in actual["records"]:
        for loc in record["locations"]:
            loc["paths"].reverse()
        for issue in record.get("issues", []):
            issue["message"] = "different wording"
    actual["unmatched"].reverse()
    assert compare_results(expected, actual) == []
    actual["records"][0]["metadata"]["subject_id"] = "m999"
    assert compare_results(expected, actual)


# --------------------------------------------------------------------------- command line

def test_cli_validate_and_walk(capsys):
    case = CONFORMANCE_DIR / "raw-processed-matching"
    assert main(["validate", str(case / "config.json")]) == 0
    assert main(["validate", str(CONFORMANCE_DIR / "invalid-schema" / "config.json")]) == 1
    capsys.readouterr()
    assert main(["walk", str(case / "config.json"), str(case / "listing.json"), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    with (case / "expected.json").open() as f:
        assert compare_results(json.load(f), out) == []
    assert main(["walk", str(case / "config.json"), str(case / "listing.json")]) == 0
    report = capsys.readouterr().out
    assert "session: 4" in report and "Unmatched: 3" in report


def test_cli_conformance(capsys):
    assert main(["conformance", str(CONFORMANCE_DIR)]) == 0
    out = capsys.readouterr().out
    case_count = sum(1 for p in CONFORMANCE_DIR.iterdir() if p.is_dir())
    assert f"{case_count} passed, 0 failed, 0 skipped" in out


def test_all_cases_run(capsys):
    results = run_cases(CONFORMANCE_DIR)
    assert {r.name for r in results} == {p.name for p in CONFORMANCE_DIR.iterdir() if p.is_dir()}


def test_token_format_zero_fills_integers():
    assert format_token(7, "05") == "00007"
    assert format_token("7", "03") == "007"
    assert format_token(123456, "05") == "123456"  # wider values keep their digits
    assert format_token(7) == "7" and format_token("00007") == "00007"
