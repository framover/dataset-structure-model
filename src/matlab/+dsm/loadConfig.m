function config = loadConfig(path, options)
%loadConfig Load and validate a config, applying a sibling <name>.local.json overlay
%
%   config = dsm.loadConfig("my-dataset.json") returns a dsm.Config.
%   Throws dsm.ConfigError when the file must be refused. When a file named
%   <name>.local.json exists next to the config, its preferences replace
%   the config's and its rootStoragePaths entries set the path of the
%   roots they name, so per-machine settings stay out of the shared file.

    arguments
        path (1,1) string
        options.RejectDraft (1,1) logical = true
    end
    doc = dsm.internal.readJson(path);
    dsm.validateConfig(doc, "RejectDraft", options.RejectDraft);
    [folder, name] = fileparts(path);
    overlayPath = fullfile(folder, name + ".local.json");
    if isfile(overlayPath)
        doc = dsm.internal.applyOverlay(doc, dsm.internal.readJson(overlayPath));
        % the overlay's preferences and paths must satisfy the schema too
        dsm.validateConfig(doc, "RejectDraft", options.RejectDraft);
    end
    config = dsm.Config(doc, path);
end
