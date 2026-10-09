classdef Walker < handle
%Walker Walk a listing into entity records
%
%   Implements the reader rules the conformance fixtures encode
%   (docs/guides/conformance.md). Mirrors the Python reference reader.

    properties (SetAccess = immutable)
        Config dsm.Config
        Registry dsm.ExtractorRegistry
    end

    properties (Access = private)
        Entities containers.Map   % key -> entity accumulator struct
        EntityKeys (1,:) string = string.empty(1, 0)   % insertion order
        Unmatched (1,:) cell = {}
        Warnings (1,:) string = string.empty(1, 0)
        Roots (1,:) cell = {}
        Trees containers.Map      % "loc|root" -> dsm.internal.Tree
    end

    methods
        function obj = Walker(config, registry)
            arguments
                config (1,1) dsm.Config
                registry (1,1) dsm.ExtractorRegistry = dsm.ExtractorRegistry()
            end
            obj.Config = config;
            obj.Registry = registry;
            obj.Entities = containers.Map("KeyType", "char", "ValueType", "any");
            obj.Trees = containers.Map("KeyType", "char", "ValueType", "any");
        end

        function result = walk(obj, listing)
            arguments
                obj
                listing (1,1) dsm.Listing
            end
            environment = listing.Environment;
            if environment == ""
                environment = string(dsm.internal.getField(obj.Config.preferences(), "environmentIdentifier", ""));
            end
            for root = listing.Roots
                rootPath = obj.Config.rootStoragePath(root{1}.DataLocation, root{1}.RootStoragePath);
                rootEnvironment = string(dsm.internal.getField(rootPath, "environment", ""));
                if environment ~= "" && rootEnvironment ~= "" && rootEnvironment ~= environment
                    obj.Warnings(end+1) = sprintf("%s/%s is for environment '%s', listing is for '%s'", ...
                        root{1}.DataLocation, root{1}.RootStoragePath, rootEnvironment, environment);
                end
                obj.Roots{end+1} = struct("DataLocation", root{1}.DataLocation, ...
                    "RootStoragePath", root{1}.RootStoragePath, "EntryCount", numel(root{1}.Entries));
                tree = dsm.internal.Tree(root{1}.Entries);
                obj.Trees(char(root{1}.DataLocation + "|" + root{1}.RootStoragePath)) = tree;
                obj.visit(root{1}.DataLocation, root{1}.RootStoragePath, tree, 1, "", {});
            end
            records = obj.finalize();
            unresolved = string.empty(1, 0);
            for key = obj.EntityKeys
                unresolved = [unresolved, obj.Entities(char(key)).Unresolved]; %#ok<AGROW>
            end
            result = dsm.WalkResult();
            result.Records = records;
            result.Unmatched = obj.sortedUnmatched();
            result.Environment = environment;
            result.Roots = obj.Roots;
            result.UnresolvedExtractors = unique(unresolved);
            result.Warnings = obj.Warnings;
        end
    end

    methods (Access = private)
        function unmatch(obj, locId, rootId, path, reason, detail)
            obj.Unmatched{end+1} = struct("dataLocationIdentifier", string(locId), ...
                "rootStoragePathIdentifier", string(rootId), "path", string(path), ...
                "reason", string(reason), "detail", string(detail));
        end

        function items = sortedUnmatched(obj)
            items = obj.Unmatched;
            if isempty(items)
                return
            end
            keys = cellfun(@(u) u.dataLocationIdentifier + "|" + u.rootStoragePathIdentifier + "|" + u.path, items);
            [~, order] = sort(keys);
            items = items(order);
        end

        function visit(obj, locId, rootId, tree, levelIndex, parentPath, ancestors)
            layout = obj.Config.layout(locId);
            level = layout{levelIndex};
            last = levelIndex == numel(layout);
            expectsDir = string(dsm.internal.getField(level, "fileSystemType", "folder")) == "folder";
            for entry = tree.children(parentPath)
                name = dsm.internal.pathBase(entry{1});
                if obj.Config.isExcluded(level, name)
                    obj.unmatch(locId, rootId, entry{1}, "excluded", sprintf("matches an excludePattern of level '%s'", level.name));
                    continue
                end
                if dsm.internal.isDirEntry(entry{1}) ~= expectsDir
                    if expectsDir
                        kind = "folder";
                    else
                        kind = "file";
                    end
                    obj.unmatch(locId, rootId, entry{1}, "no-match", sprintf("a %s is expected at level '%s'", kind, level.name));
                    continue
                end
                if ~obj.Config.nameMatches(level, name)
                    obj.unmatch(locId, rootId, entry{1}, "no-match", ...
                        sprintf("does not match level '%s' pattern %s", level.name, obj.Config.matchRegex(level)));
                    continue
                end
                entityType = string(dsm.internal.getField(level, "entityType", ""));
                if entityType == ""
                    % structural level: walked, never an entity; an innermost one covers its contents
                    if ~last
                        obj.visit(locId, rootId, tree, levelIndex + 1, entry{1}, ancestors);
                    end
                    continue
                end
                if expectsDir
                    fileSystemType = "folder";
                else
                    fileSystemType = "file";
                end
                [entityKey, identity] = obj.resolveEntity(locId, rootId, entry{1}, entityType, ancestors, fileSystemType);
                if entityKey == ""
                    obj.unmatch(locId, rootId, entry{1}, "no-match", ...
                        sprintf("identity of %s could not be extracted from '%s'", entityType, name));
                    continue
                end
                if expectsDir && ~last
                    obj.visit(locId, rootId, tree, levelIndex + 1, entry{1}, [ancestors, {{entityType, identity}}]);
                end
            end
        end

        function [entityKey, identity] = resolveEntity(obj, locId, rootId, relPath, entityType, ancestors, fileSystemType)
            config = obj.Config;
            rootPath = regexprep(string(config.rootStoragePath(locId, rootId).path), "[/\\]+$", "");
            fullPath = rootPath + "/" + regexprep(string(relPath), "/$", "");
            seed = seedFrom(ancestors);

            % ancestors that have no level of their own in this location are read from this path;
            % every field of theirs this path yields is kept for their record, not only the identity
            inferred = {};
            inferredValues = {};
            inferredUnresolved = {};
            for ancestorType = config.typesBefore(entityType)
                if any(cellfun(@(a) string(a{1}) == ancestorType, ancestors))
                    continue
                end
                if isempty(config.rulesFor(locId, ancestorType))
                    continue
                end
                [values, unresolved] = dsm.internal.evaluateFields(config, locId, relPath, ancestorType, seed, obj.Registry, fullPath);
                keys = config.identityKeys(ancestorType);
                if all(arrayfun(@(k) isfield(values, k) && ~dsm.internal.isNone(values.(k)), keys))
                    ancestorIdentity = struct();
                    for k = keys
                        ancestorIdentity.(k) = values.(k);
                        seed.(k) = values.(k);
                    end
                    inferred{end+1} = {ancestorType, ancestorIdentity}; %#ok<AGROW>
                    inferredValues{end+1} = values; %#ok<AGROW>
                    inferredUnresolved{end+1} = unresolved; %#ok<AGROW>
                end
            end
            parents = obj.sortParents([ancestors, inferred]);
            seed = seedFrom(parents);

            [values, unresolved] = dsm.internal.evaluateFields(config, locId, relPath, entityType, seed, obj.Registry, fullPath);
            keys = config.identityKeys(entityType);
            identity = struct();
            for k = keys
                if ~isfield(values, k) || dsm.internal.isNone(values.(k))
                    entityKey = "";
                    return
                end
                identity.(k) = values.(k);
            end

            entityKey = obj.getOrCreate(entityType, identity, parents);
            entity = obj.Entities(char(entityKey));
            locationKey = char(string(locId) + "|" + string(rootId));
            if isKey(entity.Locations, locationKey)
                accumulator = entity.Locations(locationKey);
            else
                accumulator = struct("FileSystemType", fileSystemType, "Paths", {{}});
                entity.LocationOrder(end+1) = string(locationKey);
            end
            accumulator.Paths{end+1} = char(relPath);
            entity.Locations(locationKey) = accumulator;
            entity.Observations{end+1} = {string(locId), values};
            entity.Unresolved = unique([entity.Unresolved, unresolved]);
            obj.Entities(char(entityKey)) = entity;

            for i = 1:numel(inferred)
                ancestorType = inferred{i}{1};
                ancestorParents = parents(cellfun(@(p) config.typeOrder(p{1}) < config.typeOrder(ancestorType), parents));
                ancestorKey = obj.getOrCreate(ancestorType, inferred{i}{2}, ancestorParents);
                ancestor = obj.Entities(char(ancestorKey));
                ancestor.Observations{end+1} = {string(locId), inferredValues{i}};
                ancestor.Unresolved = unique([ancestor.Unresolved, inferredUnresolved{i}]);
                obj.Entities(char(ancestorKey)) = ancestor;
            end
        end

        function parents = sortParents(obj, parents)
            if isempty(parents)
                return
            end
            orders = cellfun(@(p) obj.Config.typeOrder(p{1}), parents);
            [~, order] = sort(orders);
            parents = parents(order);
        end

        function key = getOrCreate(obj, entityType, identity, parents)
            key = entityKeyFor(entityType, identity, parents);
            if ~isKey(obj.Entities, char(key))
                obj.Entities(char(key)) = struct("EntityType", string(entityType), "Identity", identity, ...
                    "Parents", {parents}, "Locations", containers.Map("KeyType", "char", "ValueType", "any"), ...
                    "LocationOrder", string.empty(1, 0), "Observations", {{}}, "Unresolved", string.empty(1, 0));
                obj.EntityKeys(end+1) = key;
            end
        end

        function records = finalize(obj)
            records = cell(1, numel(obj.EntityKeys));
            sortKeys = strings(1, numel(obj.EntityKeys));
            for i = 1:numel(obj.EntityKeys)
                entity = obj.Entities(char(obj.EntityKeys(i)));
                records{i} = obj.buildRecord(entity);
                sortKeys(i) = sprintf("%03d|%s|%s", obj.Config.typeOrder(entity.EntityType), ...
                    parentsKeyFor(entity.Parents), identityKeyFor(entity.Identity));
            end
            [~, order] = sort(sortKeys);
            records = records(order);
        end

        function record = buildRecord(obj, entity)
            config = obj.Config;
            definitions = config.definitions();
            issues = {};
            metadata = seedFrom(entity.Parents);

            % own fields: union over every path the entity was read from (its own, or the descendants
            % it was inferred from), in walk order
            % Observations is {{locId, values}, ...}; unique() on the location ids keeps first occurrence order
            observedLocations = unique(cellfun(@(o) o{1}, entity.Observations), "stable");
            mappedFields = string.empty(1, 0);
            functionFields = containers.Map("KeyType", "char", "ValueType", "any");
            for locId = observedLocations
                for item = config.rulesFor(locId, entity.EntityType)
                    ref = string(item{1}.metadataRef);
                    if ~ismember(ref, mappedFields)
                        mappedFields(end+1) = ref; %#ok<AGROW>
                    end
                    if string(item{1}.extraction.method) == "function"
                        functionFields(char(ref)) = string(item{1}.extraction.extractorFunction);
                    end
                end
            end
            for field = mappedFields
                distinct = {};
                for observation = entity.Observations
                    value = dsm.internal.getField(observation{1}{2}, field, []);
                    if ~dsm.internal.isNone(value) && ~any(cellfun(@(d) isequal(d, value), distinct))
                        distinct{end+1} = value; %#ok<AGROW>
                    end
                end
                if numel(distinct) > 1
                    issues{end+1} = issue("metadata-conflict", sprintf("%s: sources disagree; using the first value", field)); %#ok<AGROW>
                end
                if ~isempty(distinct)
                    metadata.(field) = distinct{1};
                elseif isKey(functionFields, char(field)) && ismember(functionFields(char(field)), entity.Unresolved)
                    issues{end+1} = issue("unresolved-extractor", sprintf("%s: no implementation registered for '%s'", field, functionFields(char(field)))); %#ok<AGROW>
                elseif isfield(definitions.(field), "defaultValue")
                    metadata.(field) = definitions.(field).defaultValue;
                else
                    issues{end+1} = issue("extraction-failed", sprintf("%s: no value and no defaultValue", field)); %#ok<AGROW>
                end
            end
            for key = config.identityKeys(entity.EntityType)
                metadata.(key) = entity.Identity.(key);
            end
            for field = string(fieldnames(metadata))'
                problem = dsm.internal.validateValue(metadata.(field), dsm.internal.getField(definitions, field, struct()));
                if problem ~= ""
                    issues{end+1} = issue("validation-failed", sprintf("%s: %s", field, problem)); %#ok<AGROW>
                end
            end

            locations = cell(1, numel(entity.LocationOrder));
            for i = 1:numel(entity.LocationOrder)
                locationKey = entity.LocationOrder(i);
                locId = extractBefore(locationKey, "|");
                rootId = extractAfter(locationKey, "|");
                accumulator = entity.Locations(char(locationKey));
                level = config.layout(locId);
                level = level{config.entityLevelIndex(locId, entity.EntityType)};
                entry = struct("dataLocationIdentifier", locId, "rootStoragePathIdentifier", rootId, ...
                    "fileSystemType", string(accumulator.FileSystemType), "paths", {sort(accumulator.Paths)});
                if accumulator.FileSystemType == "folder" && numel(accumulator.Paths) > 1
                    % the same identity twice under one parent folder is a duplicate; under different parents
                    % (a structural level above the entity, or alternating branches) it is one entity in several places
                    parentFolders = cellfun(@(p) dsm.internal.pathParent(p), accumulator.Paths);
                    for parentFolder = unique(parentFolders)
                        count = sum(parentFolders == parentFolder);
                        if count > 1
                            issues{end+1} = issue("duplicate-entity", sprintf("%d folders under '%s' in '%s' yield the same identity", count, parentFolder, locId)); %#ok<AGROW>
                        end
                    end
                end
                if isfield(level, "filePatterns")
                    tree = obj.Trees(char(locationKey));
                    if accumulator.FileSystemType == "file"
                        candidates = sort(accumulator.Paths);
                    else
                        candidates = {};
                        for folder = accumulator.Paths
                            candidates = [candidates, tree.childFiles(folder{1})]; %#ok<AGROW>
                        end
                        candidates = sort(unique(candidates));
                    end
                    files = containers.Map("KeyType", "char", "ValueType", "any");
                    complete = true;
                    for pattern = dsm.internal.asCellOfStructs(level.filePatterns)
                        regex = substituteTokens(pattern{1}.pattern, metadata);
                        matched = candidates(cellfun(@(c) ~isempty(regexp(char(dsm.internal.pathBase(c)), regex, "once")), candidates));
                        label = string(dsm.internal.getField(pattern{1}, "name", pattern{1}.pattern));
                        if isfield(pattern{1}, "name")
                            files(char(pattern{1}.name)) = matched;
                        end
                        if dsm.internal.getField(pattern{1}, "isRequired", false) && isempty(matched)
                            complete = false;
                            issues{end+1} = issue("missing-required-file", sprintf("%s: pattern '%s' is required, matched 0", locId, label)); %#ok<AGROW>
                        end
                        if string(dsm.internal.getField(pattern{1}, "cardinality", "many")) == "one" && numel(matched) > 1
                            issues{end+1} = issue("cardinality-violation", sprintf("%s: pattern '%s' expects one file, matched %d", locId, label, numel(matched))); %#ok<AGROW>
                        end
                    end
                    entry.files = files;
                    entry.isComplete = complete;
                end
                locations{i} = entry;
            end
            if ~isempty(locations)
                locationIds = config.locationIds();
                keys = cellfun(@(l) sprintf("%03d|%s", find(locationIds == l.dataLocationIdentifier, 1), l.rootStoragePathIdentifier), locations);
                [~, order] = sort(keys);
                locations = locations(order);
            end

            parents = cell(1, numel(entity.Parents));
            for i = 1:numel(entity.Parents)
                parents{i} = struct("entityType", string(entity.Parents{i}{1}), "identity", entity.Parents{i}{2});
            end
            record = struct("entityType", entity.EntityType, "identity", entity.Identity, ...
                "parents", {parents}, "locations", {locations}, "metadata", metadata, "issues", {issues});
        end
    end
end

function seed = seedFrom(parents)
    seed = struct();
    for parent = parents
        for key = string(fieldnames(parent{1}{2}))'
            seed.(key) = parent{1}{2}.(key);
        end
    end
end

function s = issue(code, message)
    s = struct("code", string(code), "message", string(message));
end

function key = identityKeyFor(identity)
    names = sort(string(fieldnames(identity)))';
    parts = arrayfun(@(n) n + "=" + string(identity.(n)), names);
    key = strjoin(parts, ";");
end

function key = parentsKeyFor(parents)
    parts = cellfun(@(p) string(p{1}) + ":" + identityKeyFor(p{2}), parents);
    if isempty(parts)
        key = "";
    else
        key = strjoin(parts, ",");
    end
end

function key = entityKeyFor(entityType, identity, parents)
    key = string(entityType) + "|" + identityKeyFor(identity) + "|" + parentsKeyFor(parents);
end

function regex = substituteTokens(pattern, metadata)
    [tokens, literals] = regexp(char(pattern), "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens", "split");
    regex = string(literals{1});
    for i = 1:numel(tokens)
        value = string(dsm.internal.getField(metadata, tokens{i}{1}, ""));
        regex = regex + regexptranslate("escape", char(value)) + string(literals{i+1});
    end
    regex = char(regex);
end
