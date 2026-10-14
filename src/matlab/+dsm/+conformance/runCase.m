function result = runCase(caseDirectory, registry)
%runCase Run one conformance case against this reader
%
%   result = dsm.conformance.runCase(caseDirectory) returns a struct with
%   Name, Status ("pass" | "fail" | "skip") and Diffs (string array).
%   Cases that require extractors the registry lacks are skipped.

    arguments
        caseDirectory (1,1) string
        registry (1,1) dsm.ExtractorRegistry = dsm.conformance.fixtureExtractors()
    end
    [~, name] = fileparts(caseDirectory);
    configDoc = dsm.internal.readJson(fullfile(caseDirectory, "config.json"));
    expected = dsm.internal.readJson(fullfile(caseDirectory, "expected.json"));

    if isfield(expected, "error")
        try
            dsm.validateConfig(configDoc);
            actual = struct("records", {{}}, "unmatched", {{}});
        catch exception
            if isa(exception, "dsm.ConfigError")
                actual = struct("error", struct("code", exception.Code));
            else
                rethrow(exception)
            end
        end
        result = makeResult(name, dsm.compareResults(expected, actual));
        return
    end

    required = string(fieldnames(dsm.internal.getField(expected, "requiresExtractors", struct())))';
    missing = required(~arrayfun(@(k) registry.has(k), required));
    if ~isempty(missing)
        result = struct("Name", string(name), "Status", "skip", "Diffs", "extractor not registered: " + missing);
        return
    end

    try
        dsm.validateConfig(configDoc);
    catch exception
        result = struct("Name", string(name), "Status", "fail", "Diffs", "config refused: " + string(exception.message));
        return
    end
    listing = dsm.Listing.fromFile(fullfile(caseDirectory, "listing.json"));
    config = dsm.Config(configDoc, fullfile(caseDirectory, "config.json"));
    walked = dsm.walk(config, listing, registry);
    diffs = dsm.compareResults(expected, walked.toStruct("IncludeDetail", false));
    generateFile = fullfile(caseDirectory, "generate.json");
    if isfile(generateFile)
        diffs = [diffs(:)', generationDiffs(config, dsm.internal.readJson(generateFile))];
    end
    result = makeResult(name, diffs);
end

function diffs = generationDiffs(config, doc)
%generationDiffs Check each request in a case's generate.json: the generated path, or the error code
    diffs = strings(1, 0);
    requests = dsm.internal.asCellOfStructs(doc.requests);
    for i = 1:numel(requests)
        request = requests{i};
        label = sprintf("generate[%d] %s in %s", i - 1, request.entityType, request.dataLocation);
        try
            actual = "path " + dsm.generatePath(config, request.dataLocation, request.entityType, request.values);
        catch exception
            if ~isa(exception, "dsm.GenerationError")
                rethrow(exception)
            end
            actual = "error " + exception.Code;
        end
        if isfield(request.expected, "path")
            wanted = "path " + string(request.expected.path);
        else
            wanted = "error " + string(request.expected.error);
        end
        if actual ~= wanted
            diffs(end + 1) = label + ": expected " + wanted + ", got " + actual; %#ok<AGROW>
        end
    end
end

function result = makeResult(name, diffs)
    if isempty(diffs)
        status = "pass";
    else
        status = "fail";
    end
    result = struct("Name", string(name), "Status", status, "Diffs", diffs);
end
