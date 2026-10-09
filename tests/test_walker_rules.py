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


def test_records_are_ordered_by_declaration_then_key():
    doc = minimal_config()
    result = _walk(doc, ["m220/", "m220/20250523_b/", "m110/", "m110/20250523_a/"])
    assert [(r.entity_type, r.identity) for r in result.records] == [
        ("subject", {"subject_id": "m110"}), ("subject", {"subject_id": "m220"}),
        ("session", {"session_id": "a"}), ("session", {"session_id": "b"})]


def test_structural_folder_with_nothing_matching_below_is_unmatched_itself():
    doc = minimal_config()
    layout = doc["dataLocations"][0]["filesystemSource"]["entityLayout"]
    layout.insert(1, {"name": "years", "matchPattern": "^\\d{4}$"})
    result = _walk(doc, ["m110/", "m110/2025/", "m110/2025/20250523_a/",
                         "m110/2024/",                               # empty
                         "m110/2023/", "m110/2023/notes.txt",        # holds only an entry the next level rejects
                         "m110/2022/", "m110/2022/20220101_b/", "m110/2022/x.txt"])  # holds an entity: only x.txt is reported
    assert [(u.path, u.reason) for u in result.unmatched] == [
        ("m110/2022/x.txt", "no-match"), ("m110/2023/", "no-match"), ("m110/2024/", "no-match")]
    assert sorted(r.identity["session_id"] for r in result.records if r.entity_type == "session") == ["a", "b"]
