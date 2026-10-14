classdef Config
%Config Accessors over a validated config document; the document is the model
%
%   Lists (locations, levels, rules) are returned as row cell arrays of
%   scalar structs regardless of how jsondecode shaped them. Level indices
%   are 1-based inside MATLAB; the schema's 0-based integer level references
%   are converted where they are read.

    properties (SetAccess = immutable)
        Document (1,1) struct
        Source (1,1) string = ""
    end

    properties (SetAccess = immutable, Hidden)
        % The lists above, read once: a walk asks for them tens of thousands of times. Empty when the
        % document could not be indexed (an invalid one); the accessors then read the document itself.
        Index struct = struct.empty
    end

    methods
        function obj = Config(doc, source)
            arguments
                doc (1,1) struct
                source (1,1) string = ""
            end
            obj.Document = doc;
            obj.Source = source;
            try
                obj.Index = buildIndex(obj);
            catch
                obj.Index = struct.empty;
            end
        end

        function definitions = definitions(obj)
            definitions = dsm.internal.getField(obj.Document, "metadataDefinitions", struct());
        end

        function names = entityTypes(obj)
            if ~isempty(obj.Index)
                names = obj.Index.types;
                return
            end
            items = dsm.internal.asCellOfStructs(dsm.internal.getField(obj.Document, "entityTypes", {}));
            names = string(cellfun(@(e) e.name, items, "UniformOutput", false));
            names = reshape(names, 1, []);
        end

        function index = typeOrder(obj, entityType)
            index = find(obj.entityTypes() == string(entityType), 1);
            if isempty(index)
                error("dsm:config:UnknownEntityType", "Unknown entity type '%s'", entityType)
            end
        end

        function names = typesBefore(obj, entityType)
            names = obj.entityTypes();
            names = names(1:obj.typeOrder(entityType) - 1);
        end

        function keys = identityKeys(obj, entityType)
            if ~isempty(obj.Index)
                index = find(obj.Index.types == string(entityType), 1);
                if ~isempty(index)
                    keys = obj.Index.identityKeys{index};
                    return
                end
            end
            for item = dsm.internal.asCellOfStructs(obj.Document.entityTypes)
                if string(item{1}.name) == string(entityType)
                    if isfield(item{1}, "identifierRef")
                        keys = string(item{1}.identifierRef);
                    else
                        keys = string(dsm.internal.asCellstr(item{1}.identifierRefs));
                    end
                    keys = reshape(keys, 1, []);
                    return
                end
            end
            error("dsm:config:UnknownEntityType", "Unknown entity type '%s'", entityType)
        end

        function preferences = preferences(obj)
            preferences = dsm.internal.getField(obj.Document, "preferences", struct());
        end

        function locations = locations(obj)
            if ~isempty(obj.Index)
                locations = obj.Index.locations;
                return
            end
            locations = dsm.internal.asCellOfStructs(obj.Document.dataLocations);
        end

        function ids = locationIds(obj)
            if ~isempty(obj.Index)
                ids = obj.Index.locationIds;
                return
            end
            ids = string(cellfun(@(l) l.identifier, obj.locations(), "UniformOutput", false));
            ids = reshape(ids, 1, []);
        end

        function location = location(obj, locId)
            if ~isempty(obj.Index)
                index = find(obj.Index.locationIds == string(locId), 1);
                if ~isempty(index)
                    location = obj.Index.locations{index};
                    return
                end
            end
            for candidate = obj.locations()
                if string(candidate{1}.identifier) == string(locId)
                    location = candidate{1};
                    return
                end
            end
            error("dsm:config:UnknownLocation", "Unknown data location '%s'", locId)
        end

        function source = filesystem(obj, locId)
            source = obj.location(locId).filesystemSource;
        end

        function levels = layout(obj, locId)
            index = obj.indexOfLocation(locId);
            if ~isempty(index)
                levels = obj.Index.layouts{index};
                return
            end
            levels = dsm.internal.asCellOfStructs(obj.filesystem(locId).entityLayout);
        end

        function names = levelNames(obj, locId)
            names = string(cellfun(@(l) l.name, obj.layout(locId), "UniformOutput", false));
            names = reshape(names, 1, []);
        end

        function items = mapping(obj, locId)
            index = obj.indexOfLocation(locId);
            if ~isempty(index)
                items = obj.Index.mappings{index};
                return
            end
            items = dsm.internal.asCellOfStructs(dsm.internal.getField(obj.filesystem(locId), "metadataMapping", {}));
        end

        function items = rulesFor(obj, locId, entityType)
            index = obj.indexOfLocation(locId);
            if ~isempty(index)
                typeIndex = find(obj.Index.types == string(entityType), 1);
                if ~isempty(typeIndex)
                    items = obj.Index.rules{index}{typeIndex};
                    return
                end
            end
            definitions = obj.definitions();
            items = obj.mapping(locId);
            keep = cellfun(@(item) string(definitions.(item.metadataRef).ofEntity) == string(entityType), items);
            items = items(keep);
        end

        function rootPath = rootStoragePath(obj, locId, rootId)
            index = obj.indexOfLocation(locId);
            if ~isempty(index)
                rootIndex = find(obj.Index.rootIds{index} == string(rootId), 1);
                if ~isempty(rootIndex)
                    rootPath = obj.Index.roots{index}{rootIndex};
                    return
                end
            end
            for candidate = dsm.internal.asCellOfStructs(obj.filesystem(locId).rootStoragePaths)
                if string(candidate{1}.identifier) == string(rootId)
                    rootPath = candidate{1};
                    return
                end
            end
            error("dsm:config:UnknownRootPath", "Unknown root storage path '%s' in '%s'", rootId, locId)
        end

        function index = entityLevelIndex(obj, locId, entityType)
        %entityLevelIndex 1-based index of the level representing entityType, or [] when it has none
            index = [];
            levels = obj.layout(locId);
            for i = 1:numel(levels)
                if string(dsm.internal.getField(levels{i}, "entityType", "")) == string(entityType)
                    index = i;
                    return
                end
            end
        end

        function regex = matchRegex(obj, level)
        %matchRegex The regex an entry name must match at a level, derived from the template when absent
            if ~dsm.internal.getField(level, "isVariable", true)
                regex = "^" + regexptranslate("escape", char(level.fixedName)) + "$";
            elseif isfield(level, "matchPattern")
                regex = string(level.matchPattern);
            else
                template = char(level.pathComponentTemplate);
                [tokens, literals] = regexp(template, "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens", "split");
                definitions = obj.definitions();
                regex = "^" + regexptranslate("escape", literals{1});
                for i = 1:numel(tokens)
                    key = tokens{i}{1};
                    pattern = "";
                    if isfield(definitions, key) && isfield(definitions.(key), "validation")
                        pattern = string(dsm.internal.getField(definitions.(key).validation, "pattern", ""));
                    end
                    if pattern ~= ""
                        regex = regex + "(?:" + stripAnchors(pattern) + ")";
                    else
                        regex = regex + "[^/\\]+";
                    end
                    regex = regex + regexptranslate("escape", literals{i+1});
                end
                regex = regex + "$";
            end
            regex = char(regex);
        end

        function tf = isExcluded(obj, level, name) %#ok<INUSD>
            tf = false;
            for pattern = dsm.internal.asCellstr(dsm.internal.getField(level, "excludePatterns", {}))
                if ~isempty(regexp(char(name), pattern{1}, "once"))
                    tf = true;
                    return
                end
            end
        end

        function tf = nameMatches(obj, level, name)
            tf = ~isempty(regexp(char(name), obj.matchRegex(level), "once"));
        end
    end

    methods (Access = private)
        function index = indexOfLocation(obj, locId)
            index = [];
            if ~isempty(obj.Index)
                index = find(obj.Index.locationIds == string(locId), 1);
            end
        end
    end
end

function index = buildIndex(config)
    % Everything the uncached accessors would return, computed with them before Index is set
    index = struct();
    index.types = config.entityTypes();
    index.identityKeys = arrayfun(@(t) config.identityKeys(t), index.types, "UniformOutput", false);
    index.locations = config.locations();
    index.locationIds = config.locationIds();
    count = numel(index.locations);
    [index.layouts, index.mappings, index.rules, index.roots, index.rootIds] = deal(cell(1, count));
    for i = 1:count
        locId = index.locationIds(i);
        index.layouts{i} = config.layout(locId);
        index.mappings{i} = config.mapping(locId);
        index.rules{i} = arrayfun(@(t) config.rulesFor(locId, t), index.types, "UniformOutput", false);
        index.roots{i} = dsm.internal.asCellOfStructs(config.filesystem(locId).rootStoragePaths);
        index.rootIds{i} = reshape(string(cellfun(@(r) r.identifier, index.roots{i}, "UniformOutput", false)), 1, []);
    end
end

function pattern = stripAnchors(pattern)
    pattern = regexprep(pattern, "^\^", "");
    pattern = regexprep(pattern, "\$$", "");
end
