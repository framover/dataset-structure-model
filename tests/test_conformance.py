"""
Conformance fixtures are self-consistent.

This is not a reader. It checks that each case's expectation agrees with its
config and listing: the config validates, every expected path exists in the
listing, every listing entry is accounted for, and every declarative
extraction and file pattern re-evaluates to what the expectation says.
A reader that disagrees with a case is wrong; a case that fails here is wrong.
"""
import datetime as dt
import re

import jsonschema
import pytest

from conftest import CONFORMANCE_DIR, EXAMPLES_DIR, load_json
from test_reference_integrity import check_references

TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
CASE_TO_EXAMPLE = {
    "flat-session-files": "flat_session_files.json",
    "raw-processed-matching": "raw_processed_two_photon.json",
}
ERROR_CODES = {"schema-validation", "reference-integrity"}
UNMATCHED_REASONS = {"excluded", "no-match"}
EXPECTED_KEYS = {"records", "unmatched", "requiresExtractors", "error"}
SKIP = object()  # value of a function-method extraction, which the harness cannot evaluate


# --------------------------------------------------------------------------- case loading

class Case:
    def __init__(self, path):
        self.name = path.name
        self.path = path
        self.config = load_json(path / "config.json")
        self.listing = load_json(path / "listing.json")
        self.expected = load_json(path / "expected.json")

    @property
    def is_error_case(self):
        return "error" in self.expected

    @property
    def definitions(self):
        return self.config.get("metadataDefinitions", {})

    def location(self, loc_id):
        for loc in self.config["dataLocations"]:
            if loc["identifier"] == loc_id:
                return loc
        raise KeyError(loc_id)

    def layout(self, loc_id):
        return self.location(loc_id)["filesystemSource"]["entityLayout"]

    def mapping(self, loc_id):
        return self.location(loc_id)["filesystemSource"].get("metadataMapping", [])

    def entries(self, loc_id, root_id):
        for root in self.listing["roots"]:
            if root["dataLocationIdentifier"] == loc_id and root["rootStoragePathIdentifier"] == root_id:
                return root["entries"]
        raise KeyError((loc_id, root_id))

    def identity_keys(self, entity_type):
        for et in self.config.get("entityTypes", []):
            if et["name"] == entity_type:
                return [et["identifierRef"]] if "identifierRef" in et else list(et["identifierRefs"])
        raise KeyError(entity_type)

    def entity_level_index(self, loc_id, entity_type):
        layout = self.layout(loc_id)
        indices = [i for i, level in enumerate(layout) if level.get("entityType") == entity_type]
        assert len(indices) <= 1, f"{loc_id}: entity type {entity_type} appears on several levels"
        return indices[0] if indices else None


def cases():
    return sorted(p for p in CONFORMANCE_DIR.iterdir() if p.is_dir())


def pytest_generate_tests(metafunc):
    if "case" in metafunc.fixturenames:
        found = cases()
        metafunc.parametrize("case", [Case(p) for p in found], ids=[p.name for p in found])


def _errors(schema, instance):
    return list(jsonschema.Draft7Validator(schema).iter_errors(instance))


def _skip_error_case(case):
    if case.is_error_case:
        pytest.skip("error case")


# --------------------------------------------------------------------------- path helpers

def components(path):
    return path.rstrip("/").split("/")


def basename(path):
    return components(path)[-1]


def is_dir(entry):
    return entry.endswith("/")


def ancestors(entry):
    parts = components(entry)
    return ["/".join(parts[:i]) + "/" for i in range(1, len(parts))]


def descendants(entry, entries):
    return {e for e in entries if e != entry and e.startswith(entry)} if is_dir(entry) else set()


def direct_child_files(folder, entries):
    return sorted(e for e in entries if e.startswith(folder) and not is_dir(e) and "/" not in e[len(folder):])


def claimed_files(case, loc_id, root_id):
    """Files a folder entity's filePatterns claim in one root; they belong to that entity, whatever the next level says."""
    claimed = set()
    for record in case.expected["records"]:
        for loc in record["locations"]:
            if (loc["dataLocationIdentifier"], loc["rootStoragePathIdentifier"]) != (loc_id, root_id):
                continue
            if loc.get("fileSystemType", "folder") == "folder":
                for files in loc.get("files", {}).values():
                    claimed |= set(files)
    return claimed


# --------------------------------------------------------------------------- level matching

def strip_anchors(pattern):
    if pattern.startswith("^"):
        pattern = pattern[1:]
    if pattern.endswith("$"):
        pattern = pattern[:-1]
    return pattern


def match_regex(level, definitions):
    """The regex an entry name must match at this level, deriving it from the template when needed."""
    if not level.get("isVariable", True):
        return "^" + re.escape(level["fixedName"]) + "$"
    if "matchPattern" in level:
        return level["matchPattern"]
    template = level["pathComponentTemplate"]
    out, pos = "^", 0
    for m in TOKEN.finditer(template):
        out += re.escape(template[pos:m.start()])
        pattern = definitions.get(m.group(1), {}).get("validation", {}).get("pattern")
        out += "(?:" + strip_anchors(pattern) + ")" if pattern else r"[^/\\]+"
        pos = m.end()
    return out + re.escape(template[pos:]) + "$"


def is_excluded(level, name):
    return any(re.search(p, name) for p in level.get("excludePatterns", []))


def name_matches(level, name, definitions):
    return not is_excluded(level, name) and re.search(match_regex(level, definitions), name) is not None


# --------------------------------------------------------------------------- extraction

LDML_TOKENS = [("yyyy", "%Y"), ("yy", "%y"), ("MM", "%m"), ("dd", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S")]


def ldml_to_strftime(fmt):
    out, i = "", 0
    while i < len(fmt):
        if fmt[i] == "'":
            end = fmt.index("'", i + 1)
            out += fmt[i + 1:end]
            i = end + 1
            continue
        for token, directive in LDML_TOKENS:
            if fmt.startswith(token, i):
                out += directive
                i += len(token)
                break
        else:
            out += fmt[i]
            i += 1
    return out


def parse_temporal(text, fmt, data_type):
    parsed = dt.datetime.strptime(text, ldml_to_strftime(fmt))
    if data_type == "date":
        return parsed.date().isoformat()
    if data_type == "time":
        return parsed.time().isoformat()
    return parsed.isoformat()


def apply_slice(text, spec):
    start, stop = spec.split(":")
    return text[(int(start) if start else None):(int(stop) if stop else None)]


def normalize(value, rule):
    mode = rule.get("normalize", "none")
    arg = rule.get("normalizePattern", "")
    if mode == "lowercase":
        return value.lower()
    if mode == "uppercase":
        return value.upper()
    if mode == "trim":
        return value.strip()
    if mode == "strip_prefix":
        return value[len(arg):] if value.startswith(arg) else value
    if mode == "strip_suffix":
        return value[:-len(arg)] if arg and value.endswith(arg) else value
    return value


def format_token(value):
    return str(value)


def component_for(rule, layout, rel_path):
    level_ref = rule.get("entityLayoutLevel")
    if level_ref is None:
        return rel_path.rstrip("/")
    parts = components(rel_path)
    index = level_ref if isinstance(level_ref, int) else [l["name"] for l in layout].index(level_ref)
    return parts[index] if index < len(parts) else None


def extract(rule, definition, layout, rel_path, known):
    """Evaluate one rule on one path. Returns SKIP for function rules, None for no value."""
    method = rule["method"]
    if method == "function":
        return SKIP
    if method == "fixed":
        value = rule["value"]
    elif method == "template":
        try:
            value = TOKEN.sub(lambda m: format_token(known[m.group(1)]), rule["pattern"])
        except KeyError:
            return None
    else:
        component = component_for(rule, layout, rel_path)
        if component is None:
            return None
        if method == "substring":
            value = apply_slice(component, rule["pattern"])
        else:
            match = re.search(rule["pattern"], component)
            if match is None:
                return None
            value = match.group(1) if match.groups() else match.group(0)
    if isinstance(value, str):
        value = normalize(value, rule)
    data_type = definition["dataType"]
    if data_type in ("date", "time", "datetime") and rule.get("valueFormat"):
        value = parse_temporal(value, rule["valueFormat"], data_type)
    elif data_type == "integer":
        value = int(value)
    elif data_type == "number":
        value = float(value)
    return value


def evaluate_rules(case, loc_id, rel_path, entity_type, seed):
    """All rules for fields of entity_type in one location, on one path. Templates after their inputs."""
    layout = case.layout(loc_id)
    rules = [item for item in case.mapping(loc_id) if case.definitions[item["metadataRef"]]["ofEntity"] == entity_type]
    values = dict(seed)
    results = {}
    pending = list(rules)
    while pending:
        progressed = False
        for item in list(pending):
            rule = item["extraction"]
            if rule["method"] == "template" and any(t not in values for t in TOKEN.findall(rule["pattern"]) if t in {r["metadataRef"] for r in pending}):
                continue
            results[item["metadataRef"]] = extract(rule, case.definitions[item["metadataRef"]], layout, rel_path, values)
            if results[item["metadataRef"]] not in (None, SKIP):
                values[item["metadataRef"]] = results[item["metadataRef"]]
            pending.remove(item)
            progressed = True
        assert progressed, f"{case.name}: template dependency cycle in {loc_id}"
    return results


def record_identity_from_path(case, loc_id, rel_path, entity_type):
    values = evaluate_rules(case, loc_id, rel_path, entity_type, {})
    keys = case.identity_keys(entity_type)
    if any(values.get(k) in (None, SKIP) for k in keys):
        return None
    return {k: values[k] for k in keys}


# --------------------------------------------------------------------------- analysis of one record

def analyse(case, record):
    """Recompute everything the fixture claims about one record."""
    entity_type = record["entityType"]
    identity_keys = case.identity_keys(entity_type)
    parent_seed = {k: v for p in record.get("parents", []) for k, v in p["identity"].items()}
    per_field = {}          # field -> set of distinct values across locations/paths
    fields_mapped = set()   # fields some visited location has a rule for
    function_fields = set()
    codes = set()
    files_by_location = []

    for loc in record["locations"]:
        loc_id, root_id = loc["dataLocationIdentifier"], loc["rootStoragePathIdentifier"]
        entries = case.entries(loc_id, root_id)
        layout = case.layout(loc_id)
        level_index = case.entity_level_index(loc_id, entity_type)
        assert level_index is not None, f"{case.name}: {entity_type} has no level in {loc_id} but a location entry"
        level = layout[level_index]
        for item in case.mapping(loc_id):
            if case.definitions[item["metadataRef"]]["ofEntity"] == entity_type:
                fields_mapped.add(item["metadataRef"])
                if item["extraction"]["method"] == "function":
                    function_fields.add(item["metadataRef"])

        for rel_path in loc["paths"]:
            for field, value in evaluate_rules(case, loc_id, rel_path, entity_type, parent_seed).items():
                if value is not SKIP:
                    per_field.setdefault(field, set())
                    if value is not None:
                        per_field[field].add(value)

        # file patterns
        patterns = level.get("filePatterns")
        if level.get("fileSystemType", "folder") == "file":
            candidates = sorted(loc["paths"])
        else:
            candidates = sorted({f for folder in loc["paths"] for f in direct_child_files(folder, entries)})
            if len(loc["paths"]) > 1:
                codes.add("duplicate-entity")
        files, complete = {}, True
        for pattern in patterns or []:
            regex = TOKEN.sub(lambda m: re.escape(str(record["metadata"][m.group(1)])), pattern["pattern"])
            matched = sorted(c for c in candidates if re.search(regex, basename(c)))
            if "name" in pattern:
                files[pattern["name"]] = matched
            if pattern.get("isRequired") and not matched:
                complete = False
                codes.add("missing-required-file")
            if pattern.get("cardinality", "many") == "one" and len(matched) > 1:
                codes.add("cardinality-violation")
        files_by_location.append((loc, patterns is not None, files, complete))

    # an ancestor with no level in a location is inferred from its descendants' paths there, and
    # every field of its type that those paths yield attaches to it, not just the identity
    mine = {"entityType": entity_type, "identity": record["identity"]}
    for descendant in case.expected["records"]:
        if mine not in descendant.get("parents", []):
            continue
        for loc in descendant["locations"]:
            loc_id = loc["dataLocationIdentifier"]
            if case.entity_level_index(loc_id, entity_type) is not None:
                continue
            for item in case.mapping(loc_id):
                if case.definitions[item["metadataRef"]]["ofEntity"] == entity_type:
                    fields_mapped.add(item["metadataRef"])
                    if item["extraction"]["method"] == "function":
                        function_fields.add(item["metadataRef"])
            for rel_path in loc["paths"]:
                for field, value in evaluate_rules(case, loc_id, rel_path, entity_type, parent_seed).items():
                    if value is not SKIP:
                        per_field.setdefault(field, set())
                        if value is not None:
                            per_field[field].add(value)

    expected_metadata = dict(parent_seed)
    for field in fields_mapped:
        if field in function_fields:
            continue
        values = per_field.get(field, set())
        if len(values) > 1:
            codes.add("metadata-conflict")
        if values:
            expected_metadata[field] = values
        elif "defaultValue" in case.definitions[field]:
            expected_metadata[field] = {case.definitions[field]["defaultValue"]}
        else:
            codes.add("extraction-failed")
    return {
        "identity_keys": identity_keys,
        "expected_metadata": expected_metadata,
        "function_fields": function_fields,
        "codes": codes,
        "files_by_location": files_by_location,
    }


# --------------------------------------------------------------------------- tests

def test_case_has_all_files(case):
    for name in ("config.json", "listing.json", "expected.json", "README.md"):
        assert (case.path / name).is_file(), f"{case.name} lacks {name}"


def test_expected_keys(case):
    unknown = set(case.expected) - EXPECTED_KEYS
    assert not unknown, f"{case.name}: unknown keys in expected.json: {unknown}"
    if case.is_error_case:
        assert set(case.expected) == {"error"}
        assert case.expected["error"]["code"] in ERROR_CODES
    else:
        assert "records" in case.expected and "unmatched" in case.expected


def test_error_cases_fail_as_declared(case, schema):
    if not case.is_error_case:
        pytest.skip("valid case")
    code = case.expected["error"]["code"]
    schema_errors = _errors(schema, case.config)
    if code == "schema-validation":
        assert schema_errors, f"{case.name}: config unexpectedly validates"
    else:
        assert schema_errors == [], f"{case.name}: expected a reference-integrity failure, got schema errors"
        assert check_references(case.config), f"{case.name}: references unexpectedly resolve"


def test_config_is_valid_and_coherent(case, schema):
    _skip_error_case(case)
    errors = _errors(schema, case.config)
    assert errors == [], "\n".join(f"  [{e.json_path}] {e.message}" for e in errors)
    assert check_references(case.config) == []


def test_case_config_matches_example(case):
    if case.name not in CASE_TO_EXAMPLE:
        pytest.skip("case does not mirror an example")
    assert case.config == load_json(EXAMPLES_DIR / CASE_TO_EXAMPLE[case.name]), \
        f"{case.name}/config.json has drifted from examples/{CASE_TO_EXAMPLE[case.name]}"


def test_listing_is_well_formed(case, directory_listing_schema):
    _skip_error_case(case)
    errors = _errors(directory_listing_schema, case.listing)
    assert errors == [], "\n".join(f"  [{e.json_path}] {e.message}" for e in errors)
    env = case.listing.get("environmentIdentifier")
    for root in case.listing["roots"]:
        location = case.location(root["dataLocationIdentifier"])
        root_paths = {rp["identifier"]: rp for rp in location["filesystemSource"]["rootStoragePaths"]}
        assert root["rootStoragePathIdentifier"] in root_paths
        root_env = root_paths[root["rootStoragePathIdentifier"]].get("environment")
        if env is not None and root_env is not None:
            assert root_env == env, f"{case.name}: root {root['rootStoragePathIdentifier']} is for {root_env}, listing is {env}"
        entries = root["entries"]
        assert entries == sorted(entries), f"{case.name}: entries of {root['rootStoragePathIdentifier']} are not sorted"
        present = set(entries)
        for entry in entries:
            for ancestor in ancestors(entry):
                assert ancestor in present, f"{case.name}: {entry} lacks ancestor {ancestor}"


def test_records_reference_config_and_listing(case):
    _skip_error_case(case)
    for record in case.expected["records"]:
        for loc in record["locations"]:
            loc_id, root_id = loc["dataLocationIdentifier"], loc["rootStoragePathIdentifier"]
            entries = set(case.entries(loc_id, root_id))
            level = case.layout(loc_id)[case.entity_level_index(loc_id, record["entityType"])]
            expected_type = level.get("fileSystemType", "folder")
            assert loc.get("fileSystemType", "folder") == expected_type
            for path in loc["paths"]:
                assert path in entries, f"{case.name}: path {path} not in listing {loc_id}/{root_id}"
                assert is_dir(path) == (expected_type == "folder"), f"{case.name}: {path} has the wrong trailing slash"
            for name, files in loc.get("files", {}).items():
                assert files == sorted(files), f"{case.name}: files[{name}] not sorted"
                for f in files:
                    assert f in entries and not is_dir(f), f"{case.name}: files[{name}] entry {f} is not a listed file"
                    if expected_type == "file":
                        assert f in loc["paths"], f"{case.name}: files[{name}] entry {f} is not one of the entity's paths"
                    else:
                        assert any(f.startswith(p) and "/" not in f[len(p):] for p in loc["paths"]), \
                            f"{case.name}: files[{name}] entry {f} is not a direct child of the entity folder"
    for item in case.expected["unmatched"]:
        assert item["reason"] in UNMATCHED_REASONS
        assert item["path"] in set(case.entries(item["dataLocationIdentifier"], item["rootStoragePathIdentifier"]))


def test_identity_and_parents(case):
    _skip_error_case(case)
    records = case.expected["records"]
    keys = []
    for record in records:
        assert sorted(record["identity"]) == sorted(case.identity_keys(record["entityType"]))
        for k, v in record["identity"].items():
            assert record["metadata"].get(k) == v, f"{case.name}: metadata lacks identity {k}"
        for parent in record.get("parents", []):
            assert any(r["entityType"] == parent["entityType"] and r["identity"] == parent["identity"] for r in records), \
                f"{case.name}: parent {parent} of {record['identity']} has no record"
            for k, v in parent["identity"].items():
                assert record["metadata"].get(k) == v, f"{case.name}: metadata lacks parent identity {k}"
        key = (record["entityType"], tuple(sorted(record["identity"].items())),
               tuple((p["entityType"], tuple(sorted(p["identity"].items()))) for p in record.get("parents", [])))
        assert key not in keys, f"{case.name}: duplicate record {key}"
        keys.append(key)


def test_listing_fully_accounted(case):
    _skip_error_case(case)
    for root in case.listing["roots"]:
        loc_id, root_id = root["dataLocationIdentifier"], root["rootStoragePathIdentifier"]
        entries = set(root["entries"])
        covered, unmatched_cover = set(), set()
        for record in case.expected["records"]:
            for loc in record["locations"]:
                if (loc["dataLocationIdentifier"], loc["rootStoragePathIdentifier"]) != (loc_id, root_id):
                    continue
                # contents of an entity folder belong to the entity only at the innermost level;
                # children of an outer entity folder are governed by the next level, except the
                # files the entity's own filePatterns claim
                layout = case.layout(loc_id)
                innermost = case.entity_level_index(loc_id, record["entityType"]) == len(layout) - 1
                for path in loc["paths"]:
                    covered |= {path} | set(ancestors(path))
                    if innermost:
                        covered |= descendants(path, entries)
                if loc.get("fileSystemType", "folder") == "folder":
                    for files in loc.get("files", {}).values():
                        covered |= set(files)
        for item in case.expected["unmatched"]:
            if (item["dataLocationIdentifier"], item["rootStoragePathIdentifier"]) != (loc_id, root_id):
                continue
            unmatched_cover |= {item["path"]} | descendants(item["path"], entries)
        overlap = covered & unmatched_cover
        assert not overlap, f"{case.name}: entries both covered and unmatched in {loc_id}/{root_id}: {sorted(overlap)}"
        missing = entries - covered - unmatched_cover
        assert not missing, f"{case.name}: entries neither covered nor unmatched in {loc_id}/{root_id}: {sorted(missing)}"


def test_unmatched_reasons(case):
    _skip_error_case(case)
    for item in case.expected["unmatched"]:
        layout = case.layout(item["dataLocationIdentifier"])
        parts = components(item["path"])
        depth = len(parts) - 1
        name = parts[-1]
        if depth >= len(layout):
            assert item["reason"] == "no-match"
            continue
        level = layout[depth]
        if is_excluded(level, name):
            assert item["reason"] == "excluded", f"{case.name}: {item['path']} matches an excludePattern"
            continue
        assert item["reason"] == "no-match"
        wants_dir = level.get("fileSystemType", "folder") == "folder"
        type_mismatch = wants_dir != is_dir(item["path"])
        assert type_mismatch or not name_matches(level, name, case.definitions), \
            f"{case.name}: {item['path']} matches level '{level['name']}' and should be an entity"


def test_paths_match_levels(case):
    _skip_error_case(case)
    for record in case.expected["records"]:
        for loc in record["locations"]:
            loc_id = loc["dataLocationIdentifier"]
            layout = case.layout(loc_id)
            level_index = case.entity_level_index(loc_id, record["entityType"])
            for path in loc["paths"]:
                parts = components(path)
                assert len(parts) == level_index + 1, f"{case.name}: {path} is not at level {level_index}"
                for i, part in enumerate(parts):
                    assert name_matches(layout[i], part, case.definitions), \
                        f"{case.name}: component '{part}' of {path} does not match level '{layout[i]['name']}'"
            if layout[level_index].get("fileSystemType", "folder") == "file":
                assert level_index == len(layout) - 1
                # every listed file at this level with this identity is one of the entity's paths, and vice versa
                folder = "/".join(components(loc["paths"][0])[:-1])
                folder = folder + "/" if folder else ""
                entries = case.entries(loc_id, loc["rootStoragePathIdentifier"])
                level = layout[level_index]
                claimed = claimed_files(case, loc_id, loc["rootStoragePathIdentifier"])
                same_identity = sorted(
                    f for f in direct_child_files(folder, entries)
                    if f not in claimed  # claimed by the enclosing entity, never offered to this level
                    and name_matches(level, basename(f), case.definitions)
                    and record_identity_from_path(case, loc_id, f, record["entityType"]) == record["identity"]
                )
                assert sorted(loc["paths"]) == same_identity, f"{case.name}: paths of {record['identity']} should be {same_identity}"


def test_extractions_reproduce_metadata(case):
    _skip_error_case(case)
    for record in case.expected["records"]:
        result = analyse(case, record)
        metadata = record["metadata"]
        for field, values in result["expected_metadata"].items():
            if isinstance(values, set):
                assert metadata.get(field) in values, \
                    f"{case.name}: {record['entityType']} {record['identity']} metadata[{field}] = {metadata.get(field)!r}, extraction gives {values}"
            else:
                assert metadata.get(field) == values
        extra = set(metadata) - set(result["expected_metadata"]) - result["function_fields"] - set(record["identity"])
        assert not extra, f"{case.name}: {record['identity']} has metadata not produced by any rule: {extra}"
        # ancestor identity fields are extracted from the descendant's own paths
        for parent in record.get("parents", []):
            for loc in record["locations"]:
                loc_id = loc["dataLocationIdentifier"]
                for path in loc["paths"]:
                    values = evaluate_rules(case, loc_id, path, parent["entityType"], {})
                    for k, v in parent["identity"].items():
                        if values.get(k) not in (None, SKIP):
                            assert values[k] == v, f"{case.name}: {path} gives {k}={values[k]!r}, parent says {v!r}"


def test_file_patterns_reproduce_files_and_issues(case):
    _skip_error_case(case)
    for record in case.expected["records"]:
        result = analyse(case, record)
        for loc, has_patterns, files, complete in result["files_by_location"]:
            if not has_patterns:
                assert "files" not in loc and "isComplete" not in loc, f"{case.name}: files/isComplete without filePatterns"
                continue
            assert loc.get("files") == files, f"{case.name}: {record['identity']} files should be {files}"
            assert loc.get("isComplete") == complete
        actual_codes = {issue["code"] for issue in record.get("issues", [])}
        computable = {"missing-required-file", "cardinality-violation", "duplicate-entity", "metadata-conflict"}
        if not result["function_fields"]:
            computable.add("extraction-failed")
        assert actual_codes & computable == result["codes"] & computable, \
            f"{case.name}: {record['identity']} issues {sorted(actual_codes)} vs computed {sorted(result['codes'])}"
        assert actual_codes <= result["codes"] | {"extraction-failed", "unresolved-extractor", "validation-failed"}
