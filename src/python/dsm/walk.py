"""Walk a directory listing into entity records.

The rules implemented here are the ones the conformance fixtures encode
(docs/guides/conformance.md, "Reader rules the fixtures encode").
"""
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import TOKEN, Config
from .extract import ExtractorRegistry, evaluate_fields, validate_value
from .listing import Listing, Tree, basename, is_dir
from .records import Issue, LocationEntry, Record, Unmatched, WalkResult

Identity = Dict[str, Any]
Parents = List[Tuple[str, Identity]]


def _identity_key(identity: Identity):
    return tuple(sorted(identity.items()))


def _parents_key(parents: Parents):
    return tuple((t, _identity_key(i)) for t, i in parents)


class _LocationAccumulator:
    def __init__(self, file_system_type: str):
        self.file_system_type = file_system_type
        self.paths: List[str] = []


class _Entity:
    def __init__(self, entity_type: str, identity: Identity, parents: Parents):
        self.entity_type = entity_type
        self.identity = identity
        self.parents = parents
        self.locations: "OrderedDict[Tuple[str, str], _LocationAccumulator]" = OrderedDict()
        # (location, field values) per path the entity was read from, in walk order: its own paths where
        # it has a level, and the descendant paths it was inferred from where it has none
        self.observations: List[Tuple[str, Dict[str, Any]]] = []
        self.unresolved: Set[str] = set()

    @property
    def key(self):
        return (self.entity_type, _identity_key(self.identity), _parents_key(self.parents))


class Walker:
    def __init__(self, config: Config, registry: Optional[ExtractorRegistry] = None):
        self.config = config
        self.registry = registry or ExtractorRegistry()
        self._entities: "OrderedDict[tuple, _Entity]" = OrderedDict()
        self._unmatched: List[Unmatched] = []
        self._warnings: List[str] = []
        self._roots: List[Tuple[str, str, int]] = []
        self._trees: Dict[Tuple[str, str], Tree] = {}  # kept for file-pattern evaluation after the traversal

    # ----- entry point
    def walk(self, listing: Listing) -> WalkResult:
        environment = listing.environment or self.config.preferences.get("environmentIdentifier")
        for root in listing.roots:
            rp = self.config.root_storage_path(root.data_location, root.root_storage_path)
            if environment and rp.get("environment") and rp["environment"] != environment:
                self._warnings.append(
                    f"{root.data_location}/{root.root_storage_path} is for environment "
                    f"'{rp['environment']}', listing is for '{environment}'")
            self._roots.append((root.data_location, root.root_storage_path, len(root.entries)))
            self._walk_root(root.data_location, root.root_storage_path, Tree(root.entries))
        records = self._finalize()
        unresolved = set().union(*(e.unresolved for e in self._entities.values())) if self._entities else set()
        return WalkResult(records=records,
                          unmatched=sorted(self._unmatched, key=lambda u: (u.data_location, u.root_storage_path, u.path)),
                          environment=environment, roots=self._roots,
                          unresolved_extractors=unresolved, warnings=self._warnings)

    # ----- traversal
    def _walk_root(self, loc_id, root_id, tree):
        self._trees[(loc_id, root_id)] = tree
        self._visit(loc_id, root_id, tree, 0, "", [])

    def _unmatch(self, loc_id, root_id, path, reason, detail=""):
        self._unmatched.append(Unmatched(loc_id, root_id, path, reason, detail))

    def _visit(self, loc_id, root_id, tree, level_index, parent_path, ancestors: Parents):
        layout = self.config.layout(loc_id)
        level = layout[level_index]
        last = level_index == len(layout) - 1
        expects_dir = level.get("fileSystemType", "folder") == "folder"
        for entry in tree.children(parent_path):
            name = basename(entry)
            if self.config.is_excluded(level, name):
                self._unmatch(loc_id, root_id, entry, "excluded", f"matches an excludePattern of level '{level['name']}'")
                continue
            if is_dir(entry) != expects_dir:
                kind = "folder" if expects_dir else "file"
                self._unmatch(loc_id, root_id, entry, "no-match", f"a {kind} is expected at level '{level['name']}'")
                continue
            if not self.config.name_matches(level, name):
                self._unmatch(loc_id, root_id, entry, "no-match",
                              f"does not match level '{level['name']}' pattern {self.config.match_regex(level)}")
                continue
            entity_type = level.get("entityType")
            if entity_type is None:  # structural level
                if not last:
                    self._visit(loc_id, root_id, tree, level_index + 1, entry, ancestors)
                continue
            entity = self._resolve_entity(loc_id, root_id, entry, entity_type, ancestors,
                                          "folder" if expects_dir else "file")
            if entity is None:
                self._unmatch(loc_id, root_id, entry, "no-match",
                              f"identity of {entity_type} could not be extracted from '{name}'")
                continue
            if expects_dir and not last:
                self._visit(loc_id, root_id, tree, level_index + 1, entry, ancestors + [(entity_type, entity.identity)])

    def _resolve_entity(self, loc_id, root_id, rel_path, entity_type, ancestors: Parents, file_system_type):
        root_path = self.config.root_storage_path(loc_id, root_id)["path"].rstrip("/\\")
        full_path = root_path + "/" + rel_path.rstrip("/")
        seed = {k: v for _, identity in ancestors for k, v in identity.items()}

        # ancestors that have no level of their own in this location are read from this path;
        # every field of theirs this path yields is kept for their record, not only the identity
        inferred: Parents = []
        inferred_values: Dict[str, Tuple[Dict[str, Any], Set[str]]] = {}
        for ancestor_type in self.config.types_before(entity_type):
            if any(t == ancestor_type for t, _ in ancestors):
                continue
            if not self.config.rules_for(loc_id, ancestor_type):
                continue
            values, unresolved = evaluate_fields(self.config, loc_id, rel_path, ancestor_type, seed, self.registry, full_path)
            self._apply_identity_defaults(values, ancestor_type)
            keys = self.config.identity_keys(ancestor_type)
            if all(values.get(k) is not None for k in keys):
                identity = {k: values[k] for k in keys}
                inferred.append((ancestor_type, identity))
                inferred_values[ancestor_type] = (values, unresolved)
                seed.update(identity)
        parents = sorted(ancestors + inferred, key=lambda p: self.config.type_order(p[0]))
        seed = {k: v for _, identity in parents for k, v in identity.items()}

        values, unresolved = evaluate_fields(self.config, loc_id, rel_path, entity_type, seed, self.registry, full_path)
        self._apply_identity_defaults(values, entity_type)
        keys = self.config.identity_keys(entity_type)
        if any(values.get(k) is None for k in keys):
            return None
        identity = {k: values[k] for k in keys}

        entity = self._get_or_create(entity_type, identity, parents)
        accumulator = entity.locations.setdefault((loc_id, root_id), _LocationAccumulator(file_system_type))
        accumulator.paths.append(rel_path)
        entity.observations.append((loc_id, values))
        entity.unresolved |= unresolved
        for ancestor_type, ancestor_identity in inferred:
            ancestor_parents = [p for p in parents if self.config.type_order(p[0]) < self.config.type_order(ancestor_type)]
            ancestor = self._get_or_create(ancestor_type, ancestor_identity, ancestor_parents)
            ancestor_values, ancestor_unresolved = inferred_values[ancestor_type]
            ancestor.observations.append((loc_id, ancestor_values))
            ancestor.unresolved |= ancestor_unresolved
        return entity

    def _apply_identity_defaults(self, values, entity_type):
        """An identity field with no value takes its defaultValue before the identity is checked, so an
        optional part of a composite identity (a run index absent when there is one run) can default."""
        for key in self.config.identity_keys(entity_type):
            definition = self.config.definitions[key]
            if values.get(key) is None and "defaultValue" in definition:
                values[key] = definition["defaultValue"]

    def _get_or_create(self, entity_type, identity, parents) -> _Entity:
        candidate = _Entity(entity_type, identity, parents)
        return self._entities.setdefault(candidate.key, candidate)

    # ----- records
    def _finalize(self) -> List[Record]:
        records = [self._build_record(e) for e in self._entities.values()]
        records.sort(key=lambda r: (self.config.type_order(r.entity_type), _parents_key(r.parents), _identity_key(r.identity)))
        return records

    def _build_record(self, entity: _Entity) -> Record:
        cfg = self.config
        issues: List[Issue] = []
        metadata: Dict[str, Any] = {k: v for _, identity in entity.parents for k, v in identity.items()}

        # own fields: union over every path the entity was read from (its own, or the descendants it was
        # inferred from), in walk order
        mapped_fields: List[str] = []
        function_fields: Dict[str, str] = {}
        for loc_id in dict.fromkeys(loc for loc, _ in entity.observations):
            for item in cfg.rules_for(loc_id, entity.entity_type):
                if item["metadataRef"] not in mapped_fields:
                    mapped_fields.append(item["metadataRef"])
                if item["extraction"]["method"] == "function":
                    function_fields[item["metadataRef"]] = item["extraction"]["extractorFunction"]
        for field_name in mapped_fields:
            distinct: List[Any] = []
            for _, values in entity.observations:
                value = values.get(field_name)
                if value is not None and value not in distinct:
                    distinct.append(value)
            if len(distinct) > 1:
                issues.append(Issue("metadata-conflict", f"{field_name}: sources disagree {distinct}; using {distinct[0]!r}"))
            if distinct:
                metadata[field_name] = distinct[0]
            elif field_name in function_fields and function_fields[field_name] in entity.unresolved:
                issues.append(Issue("unresolved-extractor", f"{field_name}: no implementation registered for '{function_fields[field_name]}'"))
            elif "defaultValue" in cfg.definitions[field_name]:
                metadata[field_name] = cfg.definitions[field_name]["defaultValue"]
            else:
                issues.append(Issue("extraction-failed", f"{field_name}: no value and no defaultValue"))
        for key in cfg.identity_keys(entity.entity_type):
            metadata[key] = entity.identity[key]
        for field_name, value in metadata.items():
            problem = validate_value(value, cfg.definitions.get(field_name, {}))
            if problem:
                issues.append(Issue("validation-failed", f"{field_name}: {problem}"))

        locations = []
        for (loc_id, root_id), acc in entity.locations.items():
            level = cfg.layout(loc_id)[cfg.entity_level_index(loc_id, entity.entity_type)]
            entry = LocationEntry(loc_id, root_id, acc.file_system_type, sorted(acc.paths))
            if acc.file_system_type == "folder" and len(acc.paths) > 1:
                issues.append(Issue("duplicate-entity", f"{len(acc.paths)} folders in '{loc_id}' yield {entity.identity}: {sorted(acc.paths)}"))
            patterns = level.get("filePatterns")
            if patterns is not None:
                tree = self._tree_for(loc_id, root_id)
                if acc.file_system_type == "file":
                    candidates = sorted(acc.paths)
                else:
                    candidates = sorted({e for folder in acc.paths for e in tree.children(folder) if not is_dir(e)})
                files, complete = {}, True
                for pattern in patterns:
                    regex = TOKEN.sub(lambda m: re.escape(str(metadata.get(m.group(1), ""))), pattern["pattern"])
                    matched = sorted(c for c in candidates if re.search(regex, basename(c)))
                    if "name" in pattern:
                        files[pattern["name"]] = matched
                    label = pattern.get("name", pattern["pattern"])
                    if pattern.get("isRequired") and not matched:
                        complete = False
                        issues.append(Issue("missing-required-file", f"{loc_id}: pattern '{label}' is required, matched 0"))
                    if pattern.get("cardinality", "many") == "one" and len(matched) > 1:
                        issues.append(Issue("cardinality-violation", f"{loc_id}: pattern '{label}' expects one file, matched {len(matched)}"))
                entry.files = files
                entry.is_complete = complete
            locations.append(entry)
        locations.sort(key=lambda e: (cfg.location_ids.index(e.data_location), e.root_storage_path))

        return Record(entity.entity_type, dict(entity.identity), list(entity.parents), locations, metadata, issues)

    def _tree_for(self, loc_id, root_id) -> Tree:
        return self._trees[(loc_id, root_id)]


def walk(config: Config, listing: Listing, registry: Optional[ExtractorRegistry] = None) -> WalkResult:
    return Walker(config, registry).walk(listing)
