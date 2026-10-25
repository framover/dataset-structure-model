"""The extraction contract: evaluate metadataMapping rules on one entity path."""
import datetime as dt
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .config import TOKEN, Config, format_token, token_names

LDML_TOKENS = [("yyyy", "%Y"), ("yy", "%y"), ("MM", "%m"), ("dd", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S")]
TEMPORAL = ("date", "time", "datetime")


class ExtractorRegistry:
    """Implementations of `function` extraction rules, keyed by extractorFunction."""

    def __init__(self, extractors: Optional[Dict[str, Callable]] = None):
        self._functions: Dict[str, Callable] = dict(extractors or {})

    def register(self, key: str, function: Optional[Callable] = None):
        if function is None:  # decorator form
            def decorator(fn):
                self._functions[key] = fn
                return fn
            return decorator
        self._functions[key] = function
        return function

    def get(self, key: str) -> Optional[Callable]:
        return self._functions.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._functions

    def keys(self):
        return sorted(self._functions)


def ldml_to_strftime(fmt: str) -> str:
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


def parse_temporal(text: str, fmt: str, data_type: str) -> str:
    parsed = dt.datetime.strptime(text, ldml_to_strftime(fmt))
    if data_type == "date":
        return parsed.date().isoformat()
    if data_type == "time":
        return parsed.time().isoformat()
    return parsed.isoformat()


def apply_slice(text: str, spec: str) -> str:
    start, stop = spec.split(":")
    return text[(int(start) if start else None):(int(stop) if stop else None)]


def normalize(value: str, rule: dict) -> str:
    mode = rule.get("normalize", "none")
    arg = rule.get("normalizePattern", "")
    if mode == "lowercase":
        return value.lower()
    if mode == "uppercase":
        return value.upper()
    if mode == "trim":
        return value.strip()
    if mode == "strip_prefix":
        return value[len(arg):] if arg and value.startswith(arg) else value
    if mode == "strip_suffix":
        return value[:-len(arg)] if arg and value.endswith(arg) else value
    return value


def coerce(value: Any, definition: dict, rule: dict) -> Any:
    """Type a raw extracted value per the definition's dataType. None when it cannot be typed."""
    data_type = definition.get("dataType", "string")
    try:
        if data_type in TEMPORAL:
            if isinstance(value, str) and rule.get("valueFormat"):
                return parse_temporal(value, rule["valueFormat"], data_type)
            return value
        if data_type == "integer":
            return int(value)
        if data_type == "number":
            return float(value)
        if data_type == "boolean":
            return value if isinstance(value, bool) else str(value).strip().lower() in ("true", "1", "yes")
        return value
    except (ValueError, TypeError):
        return None


def validate_value(value: Any, definition: dict) -> Optional[str]:
    """A problem description when the value violates the definition's validation, else None."""
    rules = definition.get("validation")
    if not rules:
        return None
    if "enum" in rules and value not in rules["enum"]:
        return f"{value!r} is not one of {rules['enum']}"
    if isinstance(value, str):
        if "pattern" in rules and re.search(rules["pattern"], value) is None:
            return f"{value!r} does not match {rules['pattern']!r}"
        if "minLength" in rules and len(value) < rules["minLength"]:
            return f"{value!r} is shorter than {rules['minLength']}"
        if "maxLength" in rules and len(value) > rules["maxLength"]:
            return f"{value!r} is longer than {rules['maxLength']}"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in rules and value < rules["minimum"]:
            return f"{value} is below {rules['minimum']}"
        if "maximum" in rules and value > rules["maximum"]:
            return f"{value} is above {rules['maximum']}"
    return None


def level_name_for(rule: dict, level_names: List[str]) -> Optional[str]:
    ref = rule.get("entityLayoutLevel")
    if ref is None:
        return None
    return level_names[ref] if isinstance(ref, int) else ref


def component_for(rule: dict, level_names: List[str], rel_path: str) -> Optional[str]:
    """The path component a rule reads: a level's component, or the whole relative path."""
    ref = rule.get("entityLayoutLevel")
    if ref is None:
        return rel_path.rstrip("/")
    parts = rel_path.rstrip("/").split("/")
    index = ref if isinstance(ref, int) else level_names.index(ref)
    return parts[index] if index < len(parts) else None


def evaluate_fields(config: Config, loc_id: str, rel_path: str, entity_type: str, seed: Dict[str, Any],
                    registry: ExtractorRegistry, full_path: str) -> Tuple[Dict[str, Any], Set[str]]:
    """Evaluate every rule for fields of entity_type in one location on one path.

    Returns (values, unresolved): values maps each mapped field to its value or
    None; unresolved holds registry keys of function rules with no implementation.
    Templates are evaluated after the own-type fields they reference; ancestor
    identity comes in through seed.
    """
    level_names = config.level_names(loc_id)
    rules = config.rules_for(loc_id, entity_type)
    values: Dict[str, Any] = {}
    known = dict(seed)
    unresolved: Set[str] = set()
    pending = list(rules)
    pending_refs = {item["metadataRef"] for item in rules}
    while pending:
        progressed = False
        for item in list(pending):
            ref, rule = item["metadataRef"], item["extraction"]
            if rule["method"] == "template":
                deps = [t for t in token_names(rule["pattern"]) if t in pending_refs and t != ref]
                if deps:
                    continue
            value = _evaluate(rule, config.definitions[ref], level_names, rel_path, known,
                              registry, full_path, loc_id, unresolved)
            values[ref] = value
            if value is not None:
                known[ref] = value
            pending.remove(item)
            pending_refs.discard(ref)
            progressed = True
        if not progressed:  # a dependency cycle; validation rejects these, so this is defensive
            for item in pending:
                values[item["metadataRef"]] = None
            break
    return values, unresolved


def _evaluate(rule, definition, level_names, rel_path, known, registry, full_path, loc_id, unresolved):
    method = rule["method"]
    if method == "fixed":
        return coerce(rule["value"], definition, rule)
    if method == "function":
        key = rule["extractorFunction"]
        function = registry.get(key)
        if function is None:
            unresolved.add(key)
            return None
        raw = function(full_path, level_name_for(rule, level_names), loc_id)
        return None if raw is None else coerce(raw, definition, rule)
    if method == "template":
        try:
            raw = TOKEN.sub(lambda m: format_token(known[m.group(1)], m.group(2)), rule["pattern"])
        except KeyError:
            return None
    elif method == "sidecar":  # DRAFT: not implemented by this reader
        unresolved.add("sidecar")
        return None
    else:
        component = component_for(rule, level_names, rel_path)
        if component is None:
            return None
        if method == "substring":
            raw = apply_slice(component, rule["pattern"])
        else:
            match = re.search(rule["pattern"], component)
            if match is None:
                return None
            raw = match.group(1) if match.groups() else match.group(0)
    if isinstance(raw, str):
        raw = normalize(raw, rule)
    return coerce(raw, definition, rule)
