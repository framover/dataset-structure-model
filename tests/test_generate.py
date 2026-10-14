"""Path generation: the cases in conformance/*/generate.json, plus the round trip through a walk."""
import json
import pathlib

import pytest

from dsm import Config, GenerationError, generate_path, walk
from dsm.listing import Listing, Root, normalize_entries

ROOT = pathlib.Path(__file__).resolve().parent.parent / "conformance"
CASES = sorted(p for p in ROOT.iterdir() if (p / "generate.json").is_file())
REQUESTS = [(case, i, r) for case in CASES
            for i, r in enumerate(json.loads((case / "generate.json").read_text())["requests"])]


def config_of(case):
    return Config(json.loads((case / "config.json").read_text()))


@pytest.mark.parametrize("case,number,request_", REQUESTS, ids=[f"{c.name}[{i}]" for c, i, _ in REQUESTS])
def test_generate_request(case, number, request_):
    config = config_of(case)
    if "path" in request_["expected"]:
        assert generate_path(config, request_["dataLocation"], request_["entityType"], request_["values"]) \
            == request_["expected"]["path"]
    else:
        with pytest.raises(GenerationError) as error:
            generate_path(config, request_["dataLocation"], request_["entityType"], request_["values"])
        assert error.value.code == request_["expected"]["error"]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_generated_paths_walk_back_to_the_same_identity(case):
    config = config_of(case)
    for request_ in json.loads((case / "generate.json").read_text())["requests"]:
        if "path" not in request_["expected"]:
            continue
        path = request_["expected"]["path"]
        root = config.filesystem(request_["dataLocation"])["rootStoragePaths"][0]["identifier"]
        result = walk(config, Listing([Root(request_["dataLocation"], root, normalize_entries([path]))]))
        found = [r for r in result.records if r.entity_type == request_["entityType"]]
        assert found, f"{path} was not read back as a {request_['entityType']}"
        keys = config.identity_keys(request_["entityType"])
        assert {k: found[0].identity[k] for k in keys} == {k: request_["values"][k] for k in keys}
