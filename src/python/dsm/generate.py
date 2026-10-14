"""Generate where a new entity goes in a writable location (docs/guides/pipeline-integration.md).

The inverse of reading: each level up to the entity's own contributes one
path component, from its pathComponentTemplate (or fixedName), filled with
the entity's values. The generated components must match the levels'
patterns, so what is written is found again by a walk.
"""
from typing import Any, Mapping

from .config import TOKEN, Config
from .errors import GenerationError


def generate_path(config: Config, data_location: str, entity_type: str, values: Mapping[str, Any]) -> str:
    """Relative path of the entity in the location: folders end with '/', a file-level entity does not.

    `values` holds the entity's fields and its ancestors' identity, as in an
    entity record's metadata. Raises GenerationError with code
    unknown-location, not-writable, no-level, no-template, missing-value or
    name-mismatch.
    """
    if data_location not in config.location_ids:
        raise GenerationError("unknown-location", f"no data location '{data_location}'")
    location = config.location(data_location)
    if location.get("access", "read") != "readwrite":
        raise GenerationError("not-writable", f"data location '{data_location}' is not readwrite")
    index = config.entity_level_index(data_location, entity_type)
    if index is None:
        raise GenerationError("no-level", f"entity type '{entity_type}' has no level in '{data_location}'")
    components = []
    for level in config.layout(data_location)[: index + 1]:
        if not level.get("isVariable", True):
            component = level["fixedName"]
        elif "pathComponentTemplate" in level:
            component = _fill(level["pathComponentTemplate"], values, level["name"])
        else:
            raise GenerationError("no-template", f"level '{level['name']}' has no pathComponentTemplate")
        if not config.name_matches(level, component):
            raise GenerationError(
                "name-mismatch", f"'{component}' does not match level '{level['name']}' pattern {config.match_regex(level)}")
        components.append(component)
    path = "/".join(components)
    last = config.layout(data_location)[index]
    return path + "/" if last.get("fileSystemType", "folder") == "folder" else path


def _fill(template: str, values: Mapping[str, Any], level_name: str) -> str:
    def replace(match):
        name = match.group(1)
        value = values.get(name)
        if value is None:
            raise GenerationError("missing-value", f"level '{level_name}' needs '{name}', which has no value")
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    return TOKEN.sub(replace, template)
