"""
Every example validates against the schema, and the constraints the core
adds are enforced: documents that break them are rejected.
"""
import jsonschema
import pytest

from conftest import EXAMPLES_DIR, load_json, minimal_config


def _errors(schema, instance):
    return list(jsonschema.Draft7Validator(schema).iter_errors(instance))


def pytest_generate_tests(metafunc):
    if "example_path" in metafunc.fixturenames:
        paths = sorted(EXAMPLES_DIR.glob("*.json"))
        metafunc.parametrize("example_path", paths, ids=[p.name for p in paths])


def test_example_validates(example_path, schema):
    errors = _errors(schema, load_json(example_path))
    assert errors == [], (
        f"{example_path.name} has {len(errors)} validation error(s):\n"
        + "\n".join(f"  [{e.json_path}] {e.message}" for e in errors)
    )


def test_minimal_config_is_valid(schema):
    assert _errors(schema, minimal_config()) == []


def test_preferences_are_optional(schema):
    doc = minimal_config()
    assert "preferences" not in doc
    assert _errors(schema, doc) == []
    doc["preferences"] = {"defaultDataLocationIdentifier": "raw"}
    assert _errors(schema, doc) == []


def test_missing_data_locations_is_rejected(schema):
    assert _errors(schema, {"schemaVersion": "0.1.0"})


def test_wrong_data_category_is_rejected(schema):
    doc = minimal_config()
    doc["dataLocations"][0]["dataCategory"] = "not-a-real-category"
    assert _errors(schema, doc)


def test_access_enum(schema):
    doc = minimal_config()
    doc["dataLocations"][0]["access"] = "readwrite"
    assert _errors(schema, doc) == []
    doc["dataLocations"][0]["access"] = "write"
    assert _errors(schema, doc)


def test_entity_type_without_identity_is_rejected(schema):
    doc = minimal_config()
    del doc["entityTypes"][0]["identifierRef"]
    assert _errors(schema, doc)


def test_entity_type_with_both_identity_forms_is_rejected(schema):
    doc = minimal_config()
    doc["entityTypes"][0]["identifierRefs"] = ["subject_id"]
    assert _errors(schema, doc)


def test_composite_identity_is_accepted(schema):
    doc = minimal_config()
    del doc["entityTypes"][1]["identifierRef"]
    doc["entityTypes"][1]["identifierRefs"] = ["session_id"]
    assert _errors(schema, doc) == []


def test_structural_level_needs_no_entity_type(schema):
    doc = minimal_config()
    layout = doc["dataLocations"][0]["filesystemSource"]["entityLayout"]
    layout.insert(0, {"name": "dates", "matchPattern": "^\\d{4}_\\d{2}_\\d{2}$"})
    assert _errors(schema, doc) == []


def test_variable_level_needs_match_pattern_or_template(schema):
    doc = minimal_config()
    level = doc["dataLocations"][0]["filesystemSource"]["entityLayout"][0]
    del level["matchPattern"]
    assert _errors(schema, doc)
    level["pathComponentTemplate"] = "{subject_id}"
    assert _errors(schema, doc) == []


def test_fixed_level_needs_fixed_name(schema):
    doc = minimal_config()
    layout = doc["dataLocations"][0]["filesystemSource"]["entityLayout"]
    layout.append({"name": "processed", "isVariable": False})
    assert _errors(schema, doc)
    layout[-1]["fixedName"] = "processed"
    assert _errors(schema, doc) == []


@pytest.mark.parametrize("pattern", ["0:8", "9:", ":-4", ":", "-3:", "4:18"])
def test_substring_accepts_python_slices(schema, pattern):
    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][0]["extraction"]["pattern"] = pattern
    assert _errors(schema, doc) == []


@pytest.mark.parametrize("pattern", ["0:end", "1:5:2", "5", "a:b", "0:8 "])
def test_substring_rejects_non_slices(schema, pattern):
    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][0]["extraction"]["pattern"] = pattern
    assert _errors(schema, doc)


def test_fixed_requires_value(schema):
    doc = minimal_config()
    extraction = doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][0]["extraction"]
    extraction.clear()
    extraction["method"] = "fixed"
    assert _errors(schema, doc)
    extraction["value"] = "constant"
    assert _errors(schema, doc) == []


def test_function_requires_registry_key(schema):
    doc = minimal_config()
    extraction = doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][0]["extraction"]
    extraction.clear()
    extraction["method"] = "function"
    assert _errors(schema, doc)
    extraction["extractorFunction"] = "project.datalocation.getSubjectID"  # a language symbol, not a key
    assert _errors(schema, doc)
    extraction["extractorFunction"] = "subject_id_from_sciscan_path"
    assert _errors(schema, doc) == []


@pytest.mark.parametrize("method", ["filename", "filepath", "fileClass"])
def test_removed_extraction_methods_are_rejected(schema, method):
    doc = minimal_config()
    extraction = doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][0]["extraction"]
    extraction.clear()
    extraction["method"] = method
    assert _errors(schema, doc)


def test_is_available_is_rejected(schema):
    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["rootStoragePaths"][0]["isAvailable"] = True
    assert _errors(schema, doc)


def test_file_pattern_fields(schema):
    doc = minimal_config()
    level = doc["dataLocations"][0]["filesystemSource"]["entityLayout"][1]
    level["filePatterns"] = [
        {"name": "movie", "pattern": "^{session_id}_raw\\.tif$", "isRequired": True, "cardinality": "one"}
    ]
    assert _errors(schema, doc) == []
    level["filePatterns"][0]["role"] = "primary"  # from the abandoned fileClass proposal
    assert _errors(schema, doc)


def test_custom_properties_allowed_on_level_and_root_path(schema):
    doc = minimal_config()
    source = doc["dataLocations"][0]["filesystemSource"]
    source["entityLayout"][0]["customProperties"] = {"examplePath": "m110"}
    source["rootStoragePaths"][0]["customProperties"] = {"lastSeen": "2026-09-09"}
    assert _errors(schema, doc) == []
