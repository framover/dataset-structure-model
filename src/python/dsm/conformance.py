"""Run the conformance fixtures against this reader."""
import json
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

from .compare import compare_results
from .config import Config
from .errors import ConfigError, GenerationError
from .generate import generate_path
from .extract import ExtractorRegistry
from .listing import listing_from_dict
from .validate import validate_config
from .walk import walk


def _session_number_from_folder_name(full_path, level_name, data_location):
    """Contract from conformance/function-extractor: digits after 'ses-' in the level component, else None."""
    component = full_path.rstrip("/").split("/")[-1]
    remainder = component[len("ses-"):] if component.startswith("ses-") else component
    digits = ""
    for ch in remainder:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits) if digits else None


FIXTURE_EXTRACTORS = {"session_number_from_folder_name": _session_number_from_folder_name}


@dataclass
class CaseResult:
    name: str
    status: str  # "pass" | "fail" | "skip"
    diffs: List[str] = field(default_factory=list)


def run_case(case_dir: pathlib.Path, registry: Optional[ExtractorRegistry] = None) -> CaseResult:
    registry = registry or ExtractorRegistry(FIXTURE_EXTRACTORS)
    with (case_dir / "config.json").open(encoding="utf-8") as f:
        config_doc = json.load(f)
    with (case_dir / "expected.json").open(encoding="utf-8") as f:
        expected = json.load(f)

    if "error" in expected:
        try:
            validate_config(config_doc)
        except ConfigError as e:
            actual = {"error": {"code": e.code}}
        else:
            actual = {"records": [], "unmatched": []}
        diffs = compare_results(expected, actual)
        return CaseResult(case_dir.name, "pass" if not diffs else "fail", diffs)

    missing = [k for k in expected.get("requiresExtractors", {}) if k not in registry]
    if missing:
        return CaseResult(case_dir.name, "skip", [f"extractor not registered: {k}" for k in missing])

    try:
        validate_config(config_doc)
    except ConfigError as e:
        return CaseResult(case_dir.name, "fail", [f"config refused: {e}"])
    with (case_dir / "listing.json").open(encoding="utf-8") as f:
        listing = listing_from_dict(json.load(f))
    config = Config(config_doc, source=str(case_dir / "config.json"))
    result = walk(config, listing, registry)
    diffs = compare_results(expected, result.to_dict(include_detail=False))
    if (case_dir / "generate.json").is_file():
        with (case_dir / "generate.json").open(encoding="utf-8") as f:
            diffs += generation_diffs(config, json.load(f))
    return CaseResult(case_dir.name, "pass" if not diffs else "fail", diffs)


def generation_diffs(config: Config, doc: dict) -> List[str]:
    """Check each request in a case's generate.json: the generated path, or the error code."""
    diffs = []
    for number, request in enumerate(doc["requests"]):
        label = f"generate[{number}] {request['entityType']} in {request['dataLocation']}"
        try:
            actual = {"path": generate_path(config, request["dataLocation"], request["entityType"], request["values"])}
        except GenerationError as e:
            actual = {"error": e.code}
        if actual != request["expected"]:
            diffs.append(f"{label}: expected {request['expected']}, got {actual}")
    return diffs


def run_cases(conformance_dir, registry: Optional[ExtractorRegistry] = None) -> List[CaseResult]:
    root = pathlib.Path(conformance_dir)
    return [run_case(p, registry) for p in sorted(root.iterdir()) if p.is_dir() and (p / "config.json").is_file()]
