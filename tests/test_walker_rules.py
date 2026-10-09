"""
Reader rules not pinned by a fixture case, exercised on small in-memory listings.
"""
import pytest

from conftest import minimal_config
from dsm import Config, Listing, Root, walk


def _walk(doc, entries):
    return walk(Config(doc), Listing([Root("raw", "main", entries)]))


def test_metadata_conflict_between_locations():
    doc = minimal_config()
    doc["metadataDefinitions"]["note"] = {"name": "note", "dataType": "string", "ofEntity": "session"}
    source = doc["dataLocations"][0]["filesystemSource"]
    source["metadataMapping"].append({"metadataRef": "note", "extraction": {"method": "regex", "pattern": "_(.+)$", "entityLayoutLevel": "sessions"}})
    # a second location with the same layout but a different note rule
    second = {"identifier": "copy", "displayName": "Copy", "dataCategory": "processed", "sourceType": "filesystem",
              "filesystemSource": {"rootStoragePaths": [{"identifier": "main", "path": "/data/copy"}],
                                   "entityLayout": source["entityLayout"],
                                   "metadataMapping": source["metadataMapping"][:2] + [
                                       {"metadataRef": "note", "extraction": {"method": "fixed", "value": "other"}}]}}
    doc["dataLocations"].append(second)
    result = walk(Config(doc), Listing([Root("raw", "main", ["m110/", "m110/20250523_baseline/"]),
                                        Root("copy", "main", ["m110/", "m110/20250523_baseline/"])]))
    session = [r for r in result.records if r.entity_type == "session"][0]
    assert len(session.locations) == 2
    assert session.metadata["note"] == "baseline"  # first location wins
    assert {i.code for i in session.issues} == {"metadata-conflict"}


def test_validation_failed_is_reported_but_value_kept():
    doc = minimal_config()
    doc["metadataDefinitions"]["subject_id"]["validation"] = {"pattern": "^m1"}
    result = _walk(doc, ["m110/", "m220/"])
    by_id = {r.identity["subject_id"]: r for r in result.records}
    assert by_id["m220"].metadata["subject_id"] == "m220"
    assert {i.code for i in by_id["m220"].issues} == {"validation-failed"}
    assert by_id["m110"].issues == []


def test_entity_without_extractable_identity_is_unmatched():
    doc = minimal_config()
    result = _walk(doc, ["m110/", "m110/20250523_/"])  # matches the level pattern, but session_id regex needs a name
    assert [u.path for u in result.unmatched] == ["m110/20250523_/"]
    assert [r.entity_type for r in result.records] == ["subject"]


def test_structural_innermost_level_is_covered():
    doc = minimal_config()
    layout = doc["dataLocations"][0]["filesystemSource"]["entityLayout"]
    layout.append({"name": "processed", "isVariable": False, "fixedName": "processed"})
    result = _walk(doc, ["m110/", "m110/20250523_baseline/", "m110/20250523_baseline/processed/",
                         "m110/20250523_baseline/processed/x.dat", "m110/20250523_baseline/raw/"])
    assert [u.path for u in result.unmatched] == ["m110/20250523_baseline/raw/"]


def test_outer_entity_file_patterns_claim_files_before_the_next_level():
    doc = minimal_config()
    source = doc["dataLocations"][0]["filesystemSource"]
    source["entityLayout"][0]["filePatterns"] = [{"name": "notes", "pattern": "^notes\\.txt$"},
                                                 {"name": "log", "pattern": "^{subject_id}_log\\.txt$"}]
    # a file level below whose pattern and identity rule would also accept the subject's files
    source["entityLayout"][1] = {"name": "sessions", "entityType": "session", "fileSystemType": "file", "matchPattern": "\\.txt$"}
    source["metadataMapping"][1]["extraction"]["pattern"] = "^(.+)\\.txt$"
    result = _walk(doc, ["m110/", "m110/20250523_a.txt", "m110/m110_log.txt", "m110/notes.txt", "m110/readme.md"])
    subject = [r for r in result.records if r.entity_type == "subject"][0]
    assert subject.locations[0].files == {"notes": ["m110/notes.txt"], "log": ["m110/m110_log.txt"]}
    # the claimed files are neither sessions nor unmatched; the unclaimed file is still no-match
    assert [r.identity for r in result.records if r.entity_type == "session"] == [{"session_id": "20250523_a"}]
    assert [u.path for u in result.unmatched] == ["m110/readme.md"]


def test_records_are_ordered_by_declaration_then_key():
    doc = minimal_config()
    result = _walk(doc, ["m220/", "m220/20250523_b/", "m110/", "m110/20250523_a/"])
    assert [(r.entity_type, r.identity) for r in result.records] == [
        ("subject", {"subject_id": "m110"}), ("subject", {"subject_id": "m220"}),
        ("session", {"session_id": "a"}), ("session", {"session_id": "b"})]
