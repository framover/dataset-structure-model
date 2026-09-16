import copy
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
# The Python reader is importable without installation.
sys.path.insert(0, str(REPO_ROOT / "src" / "python"))
SCHEMA_PATH = REPO_ROOT / "schema" / "DatasetStructureModel.schema.json"
ENTITY_RECORD_SCHEMA_PATH = REPO_ROOT / "schema" / "EntityRecord.schema.json"
DIRECTORY_LISTING_SCHEMA_PATH = REPO_ROOT / "schema" / "DirectoryListing.schema.json"
EXAMPLES_DIR = REPO_ROOT / "examples"
CONFORMANCE_DIR = REPO_ROOT / "conformance"
DOCS_DIR = REPO_ROOT / "docs"


def load_json(path):
    with pathlib.Path(path).open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema():
    return load_json(SCHEMA_PATH)


@pytest.fixture(scope="session")
def entity_record_schema():
    return load_json(ENTITY_RECORD_SCHEMA_PATH)


@pytest.fixture(scope="session")
def directory_listing_schema():
    return load_json(DIRECTORY_LISTING_SCHEMA_PATH)


@pytest.fixture(scope="session")
def example_files():
    return sorted(EXAMPLES_DIR.glob("*.json"))


_MINIMAL_CONFIG = {
    "schemaVersion": "0.1.0",
    "entityTypes": [
        {"name": "subject", "identifierRef": "subject_id"},
        {"name": "session", "identifierRef": "session_id"},
    ],
    "metadataDefinitions": {
        "subject_id": {"name": "subject_id", "dataType": "string", "ofEntity": "subject"},
        "session_id": {"name": "session_id", "dataType": "string", "ofEntity": "session"},
    },
    "dataLocations": [
        {
            "identifier": "raw",
            "displayName": "Raw",
            "dataCategory": "raw",
            "sourceType": "filesystem",
            "filesystemSource": {
                "rootStoragePaths": [{"identifier": "main", "path": "/data/raw"}],
                "entityLayout": [
                    {"name": "subjects", "entityType": "subject", "matchPattern": "^m\\d{3}$"},
                    {"name": "sessions", "entityType": "session", "matchPattern": "^\\d{8}_.+$"},
                ],
                "metadataMapping": [
                    {
                        "metadataRef": "subject_id",
                        "extraction": {"method": "substring", "pattern": ":", "entityLayoutLevel": "subjects"},
                    },
                    {
                        "metadataRef": "session_id",
                        "extraction": {"method": "regex", "pattern": "^\\d{8}_(.+)$", "entityLayoutLevel": "sessions"},
                    },
                ],
            },
        }
    ],
}


def minimal_config():
    """A fresh copy of the smallest config that satisfies the core."""
    return copy.deepcopy(_MINIMAL_CONFIG)
