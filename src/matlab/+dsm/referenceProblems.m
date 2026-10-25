function problems = referenceProblems(doc)
%referenceProblems Cross-reference rules JSON Schema cannot express
%
%   problems = dsm.referenceProblems(doc) returns a string array of
%   problems, empty when every identity field, ofEntity, level name,
%   derivedFrom target and template token resolves, no template cycles
%   exist, and each layout's entity types follow the entityTypes
%   declaration order.

    arguments
        doc (1,1) struct
    end
    import dsm.internal.asCellOfStructs
    import dsm.internal.asCellstr
    import dsm.internal.getField

    problems = string.empty(1, 0);
    entityTypeItems = asCellOfStructs(getField(doc, "entityTypes", {}));
    entityTypes = string(cellfun(@(e) e.name, entityTypeItems, "UniformOutput", false));
    definitions = getField(doc, "metadataDefinitions", struct());
    definitionKeys = string(fieldnames(definitions))';
    locations = asCellOfStructs(getField(doc, "dataLocations", {}));
    locationIds = string(cellfun(@(l) l.identifier, locations, "UniformOutput", false));

    if numel(unique(entityTypes)) ~= numel(entityTypes)
        problems(end+1) = "entityTypes names are not unique";
    end
    if numel(unique(locationIds)) ~= numel(locationIds)
        problems(end+1) = "dataLocations identifiers are not unique";
    end
    uuids = string(cellfun(@(l) getField(l, "uuid", ""), locations, "UniformOutput", false));
    uuids = uuids(uuids ~= "");
    if numel(unique(uuids)) ~= numel(uuids)
        problems(end+1) = "dataLocations uuids are not unique";
    end

    for i = 1:numel(entityTypeItems)
        item = entityTypeItems{i};
        if isfield(item, "identifierRef")
            refs = {item.identifierRef};
        else
            refs = asCellstr(getField(item, "identifierRefs", {}));
        end
        for j = 1:numel(refs)
            ref = string(refs{j});
            if ~ismember(ref, definitionKeys)
                problems(end+1) = sprintf("entityType '%s' identity field '%s' is not in metadataDefinitions", item.name, ref); %#ok<AGROW>
            elseif string(definitions.(ref).ofEntity) ~= string(item.name)
                problems(end+1) = sprintf("entityType '%s' identity field '%s' belongs to '%s'", item.name, ref, definitions.(ref).ofEntity); %#ok<AGROW>
            end
        end
    end

    for key = definitionKeys
        ofEntity = string(definitions.(key).ofEntity);
        if ~ismember(ofEntity, entityTypes)
            problems(end+1) = sprintf("metadataDefinitions['%s'].ofEntity '%s' is not an entity type", key, ofEntity); %#ok<AGROW>
        end
    end

    for rel = asCellOfStructs(getField(doc, "entityRelationships", {}))
        for side = ["sourceEntity", "targetEntity"]
            if ~ismember(string(rel{1}.(side)), entityTypes)
                problems(end+1) = sprintf("entityRelationship %s '%s' is not an entity type", side, rel{1}.(side)); %#ok<AGROW>
            end
        end
    end

    for i = 1:numel(locations)
        location = locations{i};
        for src = asCellstr(getField(location, "derivedFrom", {}))
            if ~ismember(string(src{1}), locationIds)
                problems(end+1) = sprintf("dataLocation '%s' derivedFrom '%s' is not a data location", location.identifier, src{1}); %#ok<AGROW>
            end
        end
        if isfield(location, "filesystemSource")
            problems = [problems, filesystemProblems(string(location.identifier), location.filesystemSource, entityTypes, definitionKeys)]; %#ok<AGROW>
        end
    end

    preferences = getField(doc, "preferences", struct());
    defaultLocation = getField(preferences, "defaultDataLocationIdentifier", []);
    if ~isempty(defaultLocation) && ~ismember(string(defaultLocation), locationIds)
        problems(end+1) = sprintf("preferences.defaultDataLocationIdentifier '%s' is not a data location", defaultLocation);
    end
    environment = getField(preferences, "environmentIdentifier", []);
    if ~isempty(environment)
        environments = string.empty(1, 0);
        for location = locations
            for rootPath = asCellOfStructs(getField(getField(location{1}, "filesystemSource", struct()), "rootStoragePaths", {}))
                environments(end+1) = string(getField(rootPath{1}, "environment", "")); %#ok<AGROW>
            end
        end
        if ~ismember(string(environment), environments)
            problems(end+1) = sprintf("preferences.environmentIdentifier '%s' matches no rootStoragePath.environment", environment);
        end
    end
end

function problems = filesystemProblems(locId, source, entityTypes, definitionKeys)
    import dsm.internal.asCellOfStructs
    import dsm.internal.getField

    problems = string.empty(1, 0);
    layout = asCellOfStructs(source.entityLayout);
    levelNames = string(cellfun(@(l) l.name, layout, "UniformOutput", false));
    if numel(unique(levelNames)) ~= numel(levelNames)
        problems(end+1) = sprintf("%s: entityLayout level names are not unique", locId);
    end
    layoutTypes = string.empty(1, 0);
    for i = 1:numel(layout)
        level = layout{i};
        entityType = getField(level, "entityType", []);
        if ~isempty(entityType)
            if ~ismember(string(entityType), entityTypes)
                problems(end+1) = sprintf("%s: level '%s' entityType '%s' is not an entity type", locId, level.name, entityType); %#ok<AGROW>
            else
                layoutTypes(end+1) = string(entityType); %#ok<AGROW>
            end
        end
        if isempty(entityType) && ~isempty(getField(level, "filePatterns", {}))
            problems(end+1) = sprintf("%s: structural level '%s' has filePatterns; a level without entityType has no entity to attach files to", locId, level.name); %#ok<AGROW>
        end
        if string(getField(level, "fileSystemType", "folder")) == "file" && i ~= numel(layout)
            problems(end+1) = sprintf("%s: file level '%s' must be the last level", locId, level.name); %#ok<AGROW>
        end
        for token = templateTokens(getField(level, "pathComponentTemplate", ""))
            if ~ismember(token, definitionKeys)
                problems(end+1) = sprintf("%s: level '%s' template token '%s' is not a metadata field", locId, level.name, token); %#ok<AGROW>
            end
        end
        patterns = asCellOfStructs(getField(level, "filePatterns", {}));
        names = string.empty(1, 0);
        for pattern = patterns
            if isfield(pattern{1}, "name")
                names(end+1) = string(pattern{1}.name); %#ok<AGROW>
            end
            for token = templateTokens(pattern{1}.pattern)
                if ~ismember(token, definitionKeys)
                    problems(end+1) = sprintf("%s: filePattern '%s' token '%s' is not a metadata field", locId, pattern{1}.pattern, token); %#ok<AGROW>
                end
            end
        end
        if numel(unique(names)) ~= numel(names)
            problems(end+1) = sprintf("%s: level '%s' filePatterns names are not unique", locId, level.name); %#ok<AGROW>
        end
    end
    if numel(unique(layoutTypes)) ~= numel(layoutTypes)
        problems(end+1) = sprintf("%s: an entity type appears on more than one level", locId);
    end
    orders = arrayfun(@(t) find(entityTypes == t, 1), layoutTypes);
    if ~issorted(orders)
        problems(end+1) = sprintf("%s: entityLayout entity types must follow the entityTypes declaration order (outermost first)", locId);
    end

    rootIds = string(cellfun(@(r) r.identifier, asCellOfStructs(source.rootStoragePaths), "UniformOutput", false));
    if numel(unique(rootIds)) ~= numel(rootIds)
        problems(end+1) = sprintf("%s: rootStoragePaths identifiers are not unique", locId);
    end

    templates = containers.Map("KeyType", "char", "ValueType", "any");
    for item = asCellOfStructs(getField(source, "metadataMapping", {}))
        ref = string(item{1}.metadataRef);
        if ~ismember(ref, definitionKeys)
            problems(end+1) = sprintf("%s: metadataMapping ref '%s' is not a metadata field", locId, ref); %#ok<AGROW>
        end
        extraction = item{1}.extraction;
        levelRef = getField(extraction, "entityLayoutLevel", []);
        if ischar(levelRef) || isstring(levelRef)
            if ~ismember(string(levelRef), levelNames)
                problems(end+1) = sprintf("%s: extraction for '%s' references unknown level '%s'", locId, ref, levelRef); %#ok<AGROW>
            end
        elseif isnumeric(levelRef) && ~isempty(levelRef) && (levelRef < 0 || levelRef >= numel(layout))
            problems(end+1) = sprintf("%s: extraction for '%s' level index %d is out of range", locId, ref, levelRef); %#ok<AGROW>
        end
        if string(extraction.method) == "template"
            tokens = templateTokens(extraction.pattern);
            templates(char(ref)) = tokens;
            for token = tokens
                if ~ismember(token, definitionKeys)
                    problems(end+1) = sprintf("%s: template for '%s' token '%s' is not a metadata field", locId, ref, token); %#ok<AGROW>
                end
                if token == ref
                    problems(end+1) = sprintf("%s: template for '%s' references itself", locId, ref); %#ok<AGROW>
                end
            end
        end
    end
    problems = [problems, templateCycles(locId, templates)];
end

function tokens = templateTokens(text)
    found = regexp(char(text), "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens");
    tokens = string(cellfun(@(t) t{1}, found, "UniformOutput", false));
    tokens = reshape(tokens, 1, []);
end

function problems = templateCycles(locId, templates)
    problems = string.empty(1, 0);
    done = string.empty(1, 0);
    for ref = string(keys(templates))
        [problems, done] = visit(ref, string.empty(1, 0), templates, done, problems, locId);
    end
end

function [problems, done] = visit(ref, path, templates, done, problems, locId)
    if ismember(ref, done)
        return
    end
    if ismember(ref, path)
        problems(end+1) = sprintf("%s: template cycle %s", locId, strjoin([path, ref], " -> "));
        return
    end
    for token = templates(char(ref))
        if isKey(templates, char(token)) && token ~= ref
            [problems, done] = visit(token, [path, ref], templates, done, problems, locId);
        end
    end
    done(end+1) = ref;
end
