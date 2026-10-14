function path = generatePath(config, dataLocation, entityType, values)
%generatePath Where a new entity goes in a writable data location
%
%   path = dsm.generatePath(config, dataLocation, entityType, values) returns
%   the entity's path relative to the location's root: folders end with '/',
%   a file-level entity does not. Each level up to the entity's own gives one
%   component, from its pathComponentTemplate (or fixedName) filled with
%   values, a struct of the entity's fields and its ancestors' identity as in
%   an entity record's metadata. Every component must match its level's
%   pattern, so what is written is found again by a walk.
%
%   Throws dsm.GenerationError with Code unknown-location, not-writable,
%   no-level, no-template, missing-value or name-mismatch.

    arguments
        config (1,1) dsm.Config
        dataLocation (1,1) string
        entityType (1,1) string
        values (1,1) struct
    end
    if ~ismember(dataLocation, config.locationIds())
        throw(dsm.GenerationError("unknown-location", "no data location '" + dataLocation + "'"))
    end
    location = config.location(dataLocation);
    if string(dsm.internal.getField(location, "access", "read")) ~= "readwrite"
        throw(dsm.GenerationError("not-writable", "data location '" + dataLocation + "' is not readwrite"))
    end
    index = config.entityLevelIndex(dataLocation, entityType);
    if isempty(index)
        throw(dsm.GenerationError("no-level", "entity type '" + entityType + "' has no level in '" + dataLocation + "'"))
    end
    levels = config.layout(dataLocation);
    components = strings(1, index);
    for i = 1:index
        level = levels{i};
        if ~dsm.internal.getField(level, "isVariable", true)
            component = string(level.fixedName);
        elseif isfield(level, "pathComponentTemplate")
            component = fill(string(level.pathComponentTemplate), values, string(level.name));
        else
            throw(dsm.GenerationError("no-template", "level '" + string(level.name) + "' has no pathComponentTemplate"))
        end
        if ~config.nameMatches(level, component)
            throw(dsm.GenerationError("name-mismatch", "'" + component + "' does not match level '" ...
                + string(level.name) + "' pattern " + string(config.matchRegex(level))))
        end
        components(i) = component;
    end
    path = join(components, "/");
    if string(dsm.internal.getField(levels{index}, "fileSystemType", "folder")) == "folder"
        path = path + "/";
    end
end

function text = fill(template, values, levelName)
    [tokens, literals] = regexp(char(template), "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens", "split");
    text = string(literals{1});
    for i = 1:numel(tokens)
        name = tokens{i}{1};
        value = dsm.internal.getField(values, name, []);
        if isempty(value) || (isstring(value) && ismissing(value))
            throw(dsm.GenerationError("missing-value", "level '" + levelName + "' needs '" + name + "', which has no value"))
        end
        text = text + string(value) + string(literals{i + 1});
    end
end
