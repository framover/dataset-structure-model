"""Schema validation and the cross-reference rules JSON Schema cannot express."""
import json
import pathlib
from typing import List

import jsonschema

from .config import TOKEN, Config
from .errors import ConfigError
from .schemas import CONFIG_SCHEMA, load_schema

DRAFT_SOURCE_TYPES = {"spreadsheet", "database", "api"}


def schema_errors(doc: dict, schema_name: str = CONFIG_SCHEMA) -> List[str]:
    validator = jsonschema.Draft7Validator(load_schema(schema_name))
    return [f"[{e.json_path}] {e.message}" for e in validator.iter_errors(doc)]


def check_references(doc: dict) -> List[str]:
    """Problems with cross-references; empty when the document is coherent."""
    problems: List[str] = []
    entity_types = [e["name"] for e in doc.get("entityTypes", [])]
    entity_type_set = set(entity_types)
    definitions = doc.get("metadataDefinitions", {})
    locations = doc.get("dataLocations", [])
    location_ids = [loc["identifier"] for loc in locations]

    if len(entity_type_set) != len(entity_types):
        problems.append("entityTypes names are not unique")
    if len(set(location_ids)) != len(location_ids):
        problems.append("dataLocations identifiers are not unique")
    uuids = [loc["uuid"] for loc in locations if "uuid" in loc]
    if len(set(uuids)) != len(uuids):
        problems.append("dataLocations uuids are not unique")

    for et in doc.get("entityTypes", []):
        refs = [et["identifierRef"]] if "identifierRef" in et else et.get("identifierRefs", [])
        for ref in refs:
            if ref not in definitions:
                problems.append(f"entityType '{et['name']}' identity field '{ref}' is not in metadataDefinitions")
            elif definitions[ref]["ofEntity"] != et["name"]:
                problems.append(f"entityType '{et['name']}' identity field '{ref}' belongs to '{definitions[ref]['ofEntity']}'")

    for key, definition in definitions.items():
        if definition["ofEntity"] not in entity_type_set:
            problems.append(f"metadataDefinitions['{key}'].ofEntity '{definition['ofEntity']}' is not an entity type")

    for rel in doc.get("entityRelationships", []):
        for side in ("sourceEntity", "targetEntity"):
            if rel[side] not in entity_type_set:
                problems.append(f"entityRelationship {side} '{rel[side]}' is not an entity type")

    for loc in locations:
        for src in loc.get("derivedFrom", []):
            if src not in location_ids:
                problems.append(f"dataLocation '{loc['identifier']}' derivedFrom '{src}' is not a data location")
        source = loc.get("filesystemSource")
        if source is not None:
            problems += _check_filesystem_source(loc["identifier"], source, entity_types, definitions)

    prefs = doc.get("preferences", {})
    default_loc = prefs.get("defaultDataLocationIdentifier")
    if default_loc is not None and default_loc not in location_ids:
        problems.append(f"preferences.defaultDataLocationIdentifier '{default_loc}' is not a data location")
    env = prefs.get("environmentIdentifier")
    if env is not None:
        envs = {rp.get("environment") for loc in locations
                for rp in loc.get("filesystemSource", {}).get("rootStoragePaths", [])}
        if env not in envs:
            problems.append(f"preferences.environmentIdentifier '{env}' matches no rootStoragePath.environment")
    return problems


def _check_filesystem_source(loc_id, source, entity_types, definitions):
    problems = []
    layout = source["entityLayout"]
    level_names = [level["name"] for level in layout]
    if len(set(level_names)) != len(level_names):
        problems.append(f"{loc_id}: entityLayout level names are not unique")
    layout_types = []
    for i, level in enumerate(layout):
        et = level.get("entityType")
        if et is not None:
            if et not in entity_types:
                problems.append(f"{loc_id}: level '{level['name']}' entityType '{et}' is not an entity type")
            else:
                layout_types.append(et)
        if level.get("fileSystemType") == "file" and i != len(layout) - 1:
            problems.append(f"{loc_id}: file level '{level['name']}' must be the last level")
        for token in TOKEN.findall(level.get("pathComponentTemplate", "")):
            if token not in definitions:
                problems.append(f"{loc_id}: level '{level['name']}' template token '{token}' is not a metadata field")
        pattern_names = [fp["name"] for fp in level.get("filePatterns", []) if "name" in fp]
        if len(set(pattern_names)) != len(pattern_names):
            problems.append(f"{loc_id}: level '{level['name']}' filePatterns names are not unique")
        for fp in level.get("filePatterns", []):
            for token in TOKEN.findall(fp["pattern"]):
                if token not in definitions:
                    problems.append(f"{loc_id}: filePattern '{fp['pattern']}' token '{token}' is not a metadata field")
    if len(set(layout_types)) != len(layout_types):
        problems.append(f"{loc_id}: an entity type appears on more than one level")
    orders = [entity_types.index(t) for t in layout_types if t in entity_types]
    if orders != sorted(orders):
        problems.append(f"{loc_id}: entityLayout entity types must follow the entityTypes declaration order (outermost first)")

    root_ids = [rp["identifier"] for rp in source["rootStoragePaths"]]
    if len(set(root_ids)) != len(root_ids):
        problems.append(f"{loc_id}: rootStoragePaths identifiers are not unique")

    templates = {}
    for item in source.get("metadataMapping", []):
        ref = item["metadataRef"]
        if ref not in definitions:
            problems.append(f"{loc_id}: metadataMapping ref '{ref}' is not a metadata field")
        extraction = item["extraction"]
        level_ref = extraction.get("entityLayoutLevel")
        if isinstance(level_ref, str) and level_ref not in level_names:
            problems.append(f"{loc_id}: extraction for '{ref}' references unknown level '{level_ref}'")
        if isinstance(level_ref, int) and not 0 <= level_ref < len(layout):
            problems.append(f"{loc_id}: extraction for '{ref}' level index {level_ref} is out of range")
        if extraction["method"] == "template":
            tokens = TOKEN.findall(extraction["pattern"])
            templates[ref] = tokens
            for token in tokens:
                if token not in definitions:
                    problems.append(f"{loc_id}: template for '{ref}' token '{token}' is not a metadata field")
                if token == ref:
                    problems.append(f"{loc_id}: template for '{ref}' references itself")
    problems += _template_cycles(loc_id, templates)
    return problems


def _template_cycles(loc_id, templates):
    problems = []
    visiting, done = set(), set()

    def visit(ref, path):
        if ref in done:
            return
        if ref in visiting:
            problems.append(f"{loc_id}: template cycle {' -> '.join(path + [ref])}")
            return
        visiting.add(ref)
        for token in templates.get(ref, []):
            if token in templates and token != ref:
                visit(token, path + [ref])
        visiting.discard(ref)
        done.add(ref)

    for ref in templates:
        visit(ref, [])
    return problems


def unsupported_draft_blocks(doc: dict) -> List[str]:
    """DRAFT features this reader does not implement."""
    problems = []
    for loc in doc.get("dataLocations", []):
        if loc.get("sourceType") in DRAFT_SOURCE_TYPES:
            problems.append(f"dataLocation '{loc['identifier']}': sourceType '{loc['sourceType']}' is DRAFT and not supported")
        for level in loc.get("filesystemSource", {}).get("entityLayout", []):
            if level.get("isRequired") is False:
                problems.append(f"dataLocation '{loc['identifier']}': level '{level['name']}' isRequired false is DRAFT and not supported")
        for item in loc.get("filesystemSource", {}).get("metadataMapping", []):
            if item["extraction"]["method"] == "sidecar":
                problems.append(f"dataLocation '{loc['identifier']}': extraction method 'sidecar' for '{item['metadataRef']}' is DRAFT and not supported")
    return problems


def validate_config(doc: dict, reject_draft: bool = True) -> None:
    """Raise ConfigError with a conformance error code when the document must be refused."""
    errors = schema_errors(doc)
    if errors:
        raise ConfigError("schema-validation", errors)
    problems = check_references(doc)
    if problems:
        raise ConfigError("reference-integrity", problems)
    if reject_draft:
        drafts = unsupported_draft_blocks(doc)
        if drafts:
            raise ConfigError("unsupported-draft", drafts)


def load_config(path, reject_draft: bool = True) -> Config:
    """Load, validate, and apply a sibling '<name>.local.json' overlay's preferences."""
    path = pathlib.Path(path)
    with path.open(encoding="utf-8") as f:
        doc = json.load(f)
    validate_config(doc, reject_draft=reject_draft)
    overlay = path.with_name(path.stem + ".local.json")
    if overlay.is_file():
        with overlay.open(encoding="utf-8") as f:
            local = json.load(f)
        if "preferences" in local:
            doc = dict(doc, preferences=local["preferences"])
    return Config(doc, source=str(path))
