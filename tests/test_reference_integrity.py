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


@pytest.mark.parametrize("pattern,expected", [
    ({"isRequired": False, "minCount": 1}, "isRequired false and minCount 1 disagree"),
    ({"isRequired": True, "minCount": 0}, "isRequired true and minCount 0 disagree"),
    ({"cardinality": "one", "maxCount": 3}, "cardinality 'one' and maxCount 3 disagree"),
    ({"cardinality": "many", "maxCount": 1}, "cardinality 'many' and maxCount 1 disagree"),
    ({"minCount": 3, "maxCount": 2}, "minCount 3 exceeds maxCount 2"),
])
def test_checker_rejects_file_counts_that_disagree(pattern, expected):
    from conftest import minimal_config

    doc = minimal_config()
    doc["dataLocations"][0]["filesystemSource"]["entityLayout"][1]["filePatterns"] = [dict(pattern, name="planes", pattern="^plane\\d\\.tif$")]
    assert any(expected in p for p in check_references(doc)), check_references(doc)
    agreeing = {"isRequired": True, "minCount": 3, "cardinality": "many", "maxCount": 3, "name": "planes", "pattern": "^plane\\d\\.tif$"}
    doc["dataLocations"][0]["filesystemSource"]["entityLayout"][1]["filePatterns"] = [agreeing]
    assert check_references(doc) == []
