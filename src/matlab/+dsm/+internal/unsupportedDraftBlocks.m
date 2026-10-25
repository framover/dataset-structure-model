function problems = unsupportedDraftBlocks(doc)
%unsupportedDraftBlocks DRAFT features this reader does not implement
    import dsm.internal.asCellOfStructs
    import dsm.internal.getField

    problems = string.empty(1, 0);
    for location = asCellOfStructs(getField(doc, "dataLocations", {}))
        sourceType = string(getField(location{1}, "sourceType", "filesystem"));
        if ismember(sourceType, ["spreadsheet", "database", "api"])
            problems(end+1) = sprintf("dataLocation '%s': sourceType '%s' is DRAFT and not supported", location{1}.identifier, sourceType); %#ok<AGROW>
        end
        for level = asCellOfStructs(getField(getField(location{1}, "filesystemSource", struct()), "entityLayout", {}))
            isRequired = getField(level{1}, "isRequired", true);
            if ~isempty(isRequired) && ~logical(isRequired)
                problems(end+1) = sprintf("dataLocation '%s': level '%s' isRequired false is DRAFT and not supported", location{1}.identifier, level{1}.name); %#ok<AGROW>
            end
        end
        for item = asCellOfStructs(getField(getField(location{1}, "filesystemSource", struct()), "metadataMapping", {}))
            if string(item{1}.extraction.method) == "sidecar"
                problems(end+1) = sprintf("dataLocation '%s': extraction method 'sidecar' for '%s' is DRAFT and not supported", location{1}.identifier, item{1}.metadataRef); %#ok<AGROW>
            end
        end
    end
end
