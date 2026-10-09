function doc = applyOverlay(doc, local)
%applyOverlay Merge a <name>.local.json overlay into a validated config document
%
%   The overlay holds preferences, which replace the config's, and
%   rootStoragePaths entries {dataLocationIdentifier, rootStoragePathIdentifier,
%   path}, which set the path of the root they name. Throws dsm.ConfigError
%   "schema-validation" for a malformed overlay and "reference-integrity" for
%   an entry that names no root path of the config.

    import dsm.internal.asCellOfStructs

    if ~(isstruct(local) && isscalar(local))
        throw(dsm.ConfigError("schema-validation", "the overlay must be a JSON object"))
    end
    unknown = setdiff(string(fieldnames(local))', ["preferences", "rootStoragePaths"]);
    if ~isempty(unknown)
        throw(dsm.ConfigError("schema-validation", ...
            "overlay: unknown key(s) " + strjoin(unknown, ", ") + "; an overlay holds preferences and rootStoragePaths only"))
    end
    if isfield(local, "preferences")
        doc.preferences = local.preferences;
    end
    if ~isfield(local, "rootStoragePaths")
        return
    end
    entries = local.rootStoragePaths;
    if ~(isstruct(entries) || iscell(entries) || isempty(entries))
        throw(dsm.ConfigError("schema-validation", "overlay: rootStoragePaths must be a list of objects with the strings dataLocationIdentifier, rootStoragePathIdentifier and path"))
    end
    problems = string.empty(1, 0);
    locations = asCellOfStructs(doc.dataLocations);
    for entry = asCellOfStructs(entries)
        for key = ["dataLocationIdentifier", "rootStoragePathIdentifier", "path"]
            if ~(isstruct(entry{1}) && isfield(entry{1}, key) && (ischar(entry{1}.(key)) || isstring(entry{1}.(key))))
                throw(dsm.ConfigError("schema-validation", "overlay: rootStoragePaths must be a list of objects with the strings dataLocationIdentifier, rootStoragePathIdentifier and path"))
            end
        end
        found = false;
        for i = 1:numel(locations)
            if string(locations{i}.identifier) ~= string(entry{1}.dataLocationIdentifier) || ~isfield(locations{i}, "filesystemSource")
                continue
            end
            roots = asCellOfStructs(locations{i}.filesystemSource.rootStoragePaths);
            for j = 1:numel(roots)
                if string(roots{j}.identifier) == string(entry{1}.rootStoragePathIdentifier)
                    roots{j}.path = char(entry{1}.path);
                    found = true;
                end
            end
            locations{i}.filesystemSource.rootStoragePaths = roots;
        end
        if ~found
            problems(end+1) = sprintf("overlay rootStoragePaths entry '%s/%s' names no root path of the config", ...
                entry{1}.dataLocationIdentifier, entry{1}.rootStoragePathIdentifier); %#ok<AGROW>
        end
    end
    if ~isempty(problems)
        throw(dsm.ConfigError("reference-integrity", problems))
    end
    doc.dataLocations = locations;
end
