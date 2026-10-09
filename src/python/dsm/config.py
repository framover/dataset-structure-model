"""Accessors over a validated config document. The document itself is the model."""
import re
from typing import Dict, List, Optional

# {name} or {name:0Nd}: group 1 is the field key, group 2 the digits of the zero-fill width or None
TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::(0[1-9][0-9]*)d)?\}")


def token_names(text: str) -> List[str]:
    return [m.group(1) for m in TOKEN.finditer(text)]


def format_token(value, width: Optional[str] = None) -> str:
    """The text a token substitutes: the value as is, or, with a `:0Nd` format, the integer zero-filled to N digits."""
    if width is None:
        return str(value)
    return format(int(value), f"0{int(width)}d")


def strip_anchors(pattern):
    if pattern.startswith("^"):
        pattern = pattern[1:]
    if pattern.endswith("$"):
        pattern = pattern[:-1]
    return pattern


class Config:
    def __init__(self, doc: dict, source: Optional[str] = None):
        self.doc = doc
        self.source = source
        self._match_cache: Dict[int, str] = {}

    # ----- top level
    @property
    def definitions(self) -> dict:
        return self.doc.get("metadataDefinitions", {})

    @property
    def entity_types(self) -> List[str]:
        return [e["name"] for e in self.doc.get("entityTypes", [])]

    def type_order(self, entity_type: str) -> int:
        return self.entity_types.index(entity_type)

    def types_before(self, entity_type: str) -> List[str]:
        return self.entity_types[: self.type_order(entity_type)]

    def identity_keys(self, entity_type: str) -> List[str]:
        for et in self.doc.get("entityTypes", []):
            if et["name"] == entity_type:
                return [et["identifierRef"]] if "identifierRef" in et else list(et["identifierRefs"])
        raise KeyError(entity_type)

    @property
    def preferences(self) -> dict:
        return self.doc.get("preferences", {})

    # ----- locations
    @property
    def locations(self) -> List[dict]:
        return self.doc["dataLocations"]

    @property
    def location_ids(self) -> List[str]:
        return [loc["identifier"] for loc in self.locations]

    def location(self, loc_id: str) -> dict:
        for loc in self.locations:
            if loc["identifier"] == loc_id:
                return loc
        raise KeyError(loc_id)

    def filesystem(self, loc_id: str) -> dict:
        return self.location(loc_id)["filesystemSource"]

    def layout(self, loc_id: str) -> List[dict]:
        return self.filesystem(loc_id)["entityLayout"]

    def level_names(self, loc_id: str) -> List[str]:
        return [level["name"] for level in self.layout(loc_id)]

    def mapping(self, loc_id: str) -> List[dict]:
        return self.filesystem(loc_id).get("metadataMapping", [])

    def rules_for(self, loc_id: str, entity_type: str) -> List[dict]:
        return [item for item in self.mapping(loc_id)
                if self.definitions[item["metadataRef"]]["ofEntity"] == entity_type]

    def root_storage_path(self, loc_id: str, root_id: str) -> dict:
        for rp in self.filesystem(loc_id)["rootStoragePaths"]:
            if rp["identifier"] == root_id:
                return rp
        raise KeyError((loc_id, root_id))

    def entity_level_index(self, loc_id: str, entity_type: str) -> Optional[int]:
        for i, level in enumerate(self.layout(loc_id)):
            if level.get("entityType") == entity_type:
                return i
        return None

    # ----- level matching
    def match_regex(self, level: dict) -> str:
        """The regex an entry name must match at this level; derived from the template when absent."""
        key = id(level)
        if key in self._match_cache:
            return self._match_cache[key]
        if not level.get("isVariable", True):
            regex = "^" + re.escape(level["fixedName"]) + "$"
        elif "matchPattern" in level:
            regex = level["matchPattern"]
        else:
            template = level["pathComponentTemplate"]
            out, pos = "^", 0
            for m in TOKEN.finditer(template):
                out += re.escape(template[pos:m.start()])
                pattern = self.definitions.get(m.group(1), {}).get("validation", {}).get("pattern")
                if m.group(2):  # a zero-filled integer: at least that many digits
                    out += r"\d{" + str(int(m.group(2))) + ",}"
                else:
                    out += "(?:" + strip_anchors(pattern) + ")" if pattern else r"[^/\\]+"
                pos = m.end()
            regex = out + re.escape(template[pos:]) + "$"
        self._match_cache[key] = regex
        return regex

    def is_excluded(self, level: dict, name: str) -> bool:
        return any(re.search(p, name) for p in level.get("excludePatterns", []))

    def name_matches(self, level: dict, name: str) -> bool:
        return re.search(self.match_regex(level), name) is not None
