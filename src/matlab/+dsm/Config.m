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

    methods
        function obj = Config(doc, source)
            arguments
                doc (1,1) struct
                source (1,1) string = ""
            end
            obj.Document = doc;
            obj.Source = source;
        end

        function definitions = definitions(obj)
            definitions = dsm.internal.getField(obj.Document, "metadataDefinitions", struct());
        end

        function names = entityTypes(obj)
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
            locations = dsm.internal.asCellOfStructs(obj.Document.dataLocations);
        end

        function ids = locationIds(obj)
            ids = string(cellfun(@(l) l.identifier, obj.locations(), "UniformOutput", false));
            ids = reshape(ids, 1, []);
        end

        function location = location(obj, locId)
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
            levels = dsm.internal.asCellOfStructs(obj.filesystem(locId).entityLayout);
        end

        function names = levelNames(obj, locId)
            names = string(cellfun(@(l) l.name, obj.layout(locId), "UniformOutput", false));
            names = reshape(names, 1, []);
        end

        function items = mapping(obj, locId)
            items = dsm.internal.asCellOfStructs(dsm.internal.getField(obj.filesystem(locId), "metadataMapping", {}));
        end

        function items = rulesFor(obj, locId, entityType)
            definitions = obj.definitions();
            items = obj.mapping(locId);
            keep = cellfun(@(item) string(definitions.(item.metadataRef).ofEntity) == string(entityType), items);
            items = items(keep);
        end

        function rootPath = rootStoragePath(obj, locId, rootId)
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
                [names, widths, literals] = dsm.internal.tokenParts(level.pathComponentTemplate);
                definitions = obj.definitions();
                regex = "^" + regexptranslate("escape", literals{1});
                for i = 1:numel(names)
                    key = names(i);
                    pattern = "";
                    if isfield(definitions, key) && isfield(definitions.(key), "validation")
                        pattern = string(dsm.internal.getField(definitions.(key).validation, "pattern", ""));
                    end
                    if ~isnan(widths(i))
                        % a zero-filled integer: at least that many digits
                        regex = regex + "\d{" + string(widths(i)) + ",}";
                    elseif pattern ~= ""
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
end

function pattern = stripAnchors(pattern)
    pattern = regexprep(pattern, "^\^", "");
    pattern = regexprep(pattern, "\$$", "");
end
