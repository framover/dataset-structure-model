function doc = minimalConfigDoc()
%minimalConfigDoc The smallest config that satisfies the core (mirrors tests/conftest.py)
    doc = jsondecode(fileread(fullfile(fileparts(mfilename("fullpath")), "minimal_config.json")));
end
