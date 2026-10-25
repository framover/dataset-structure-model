"""
Cross-reference rules JSON Schema cannot express, implemented in dsm.validate.
Every example must satisfy them; readers enforce the same rules.
"""
import pytest

from conftest import EXAMPLES_DIR, load_json
from dsm.validate import check_references  # re-exported for test_docs_snippets


def pytest_generate_tests(metafunc):
    if "example_path" in metafunc.fixturenames:
        paths = sorted(EXAMPLES_DIR.glob("*.json"))
        metafunc.parametrize("example_path", paths, ids=[p.name for p in paths])


def test_example_references_are_coherent(example_path):
    problems = check_references(load_json(example_path))
    assert problems == [], f"{example_path.name}:\n  " + "\n  ".join(problems)


def test_checker_detects_dangling_references():
    from conftest import minimal_config

    doc = minimal_config()
    doc["entityTypes"][0]["identifierRef"] = "missing"
    doc["dataLocations"][0]["filesystemSource"]["metadataMapping"][1]["extraction"]["entityLayoutLevel"] = "nope"
    doc["dataLocations"][0]["derivedFrom"] = ["ghost"]
    problems = check_references(doc)
    assert any("identity field 'missing'" in p for p in problems)
    assert any("unknown level 'nope'" in p for p in problems)
    assert any("derivedFrom 'ghost'" in p for p in problems)


def test_checker_detects_template_cycles():
    from conftest import minimal_config

    doc = minimal_config()
    doc["metadataDefinitions"]["a"] = {"name": "a", "dataType": "string", "ofEntity": "session"}
    doc["metadataDefinitions"]["b"] = {"name": "b", "dataType": "string", "ofEntity": "session"}
    mapping = doc["dataLocations"][0]["filesystemSource"]["metadataMapping"]
    mapping.append({"metadataRef": "a", "extraction": {"method": "template", "pattern": "{b}-x"}})
    mapping.append({"metadataRef": "b", "extraction": {"method": "template", "pattern": "{a}-y"}})
    assert any("template cycle" in p for p in check_references(doc))


def test_checker_requires_layout_order_to_follow_declaration_order():
    from conftest import minimal_config

    doc = minimal_config()
    layout = doc["dataLocations"][0]["filesystemSource"]["entityLayout"]
    layout.reverse()  # sessions above subjects, but subject is declared first
    assert any("declaration order" in p for p in check_references(doc))


def test_checker_allows_a_default_only_on_a_composite_identity():
    from conftest import minimal_config

    doc = minimal_config()
    doc["metadataDefinitions"]["session_id"]["defaultValue"] = "unknown"
    assert any("has a defaultValue" in p for p in check_references(doc))
    del doc["metadataDefinitions"]["session_id"]["defaultValue"]
    doc["metadataDefinitions"]["run"] = {"name": "run", "dataType": "integer", "ofEntity": "session", "defaultValue": 1}
    doc["entityTypes"][1] = {"name": "session", "identifierRefs": ["session_id", "run"]}
    assert check_references(doc) == []


def test_checker_rejects_a_default_on_every_part_of_a_composite_identity():
    from conftest import minimal_config

    doc = minimal_config()
    doc["metadataDefinitions"]["run"] = {"name": "run", "dataType": "integer", "ofEntity": "session", "defaultValue": 1}
    doc["entityTypes"][1] = {"name": "session", "identifierRefs": ["session_id", "run"]}
    doc["metadataDefinitions"]["session_id"]["defaultValue"] = "rest"
    assert any("all have a defaultValue" in p for p in check_references(doc))
    doc["metadataDefinitions"]["session_id"]["defaultValue"] = None  # a null default is no default
    assert check_references(doc) == []


def test_checker_rejects_a_default_whose_type_does_not_match_the_data_type():
    from conftest import minimal_config

    def problems_for(data_type, default):
        doc = minimal_config()
        doc["metadataDefinitions"]["experiment"] = {"name": "experiment", "dataType": data_type, "ofEntity": "session",
                                                     "defaultValue": default}
        return [p for p in check_references(doc) if "does not match dataType" in p]

    assert problems_for("integer", "1") == ["metadataDefinitions['experiment'].defaultValue \"1\" does not match dataType 'integer'"]
    assert problems_for("integer", 1.5) and problems_for("integer", True)
    assert problems_for("integer", 1) == [] and problems_for("integer", 1.0) == []
    assert problems_for("number", "1.5") and problems_for("number", False)
    assert problems_for("number", 1.5) == [] and problems_for("number", 2) == []
    assert problems_for("boolean", 1) and problems_for("boolean", "true")
    assert problems_for("boolean", True) == []
    for text_type in ("string", "date", "time", "datetime"):
        assert problems_for(text_type, 1) and problems_for(text_type, "x") == []
    assert problems_for("array", "x") and problems_for("object", 1)
    assert problems_for("integer", None) == []  # a null default is no default
