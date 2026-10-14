classdef GenerationError < MException
%GenerationError A location that cannot be generated for an entity; Code is a generation error code
%
%   Codes: "unknown-location", "not-writable", "no-level", "no-template",
%   "missing-value", "name-mismatch". The MException identifier is
%   dsm:generate:<code in camelCase>.

    properties (SetAccess = immutable)
        Code (1,1) string
    end

    methods
        function obj = GenerationError(code, message)
            arguments
                code (1,1) string
                message (1,1) string
            end
            mnemonic = regexprep(code, "-(\w)", "${upper($1)}");
            obj@MException("dsm:generate:" + mnemonic, "%s: %s", code, message);
            obj.Code = code;
        end
    end
end
