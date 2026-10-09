function [names, widths, literals] = tokenParts(text)
%tokenParts Split a template or pattern into its {token} references and the literal text between them
%
%   [names, widths, literals] = tokenParts(text). A token is {name} or
%   {name:0Nd}; names holds the field keys, widths the N of each format or
%   NaN for a token without one, and literals (one more than the tokens)
%   the text before, between and after them.

    % the format is captured whole (":05d") because regexp drops a capture that sits inside an optional
    % non-capturing group; an optional capturing group reports '' when the token has no format
    [tokens, literals] = regexp(char(text), "\{([A-Za-z_][A-Za-z0-9_]*)(:0[1-9][0-9]*d)?\}", "tokens", "split");
    names = strings(1, numel(tokens));
    widths = nan(1, numel(tokens));
    for i = 1:numel(tokens)
        names(i) = string(tokens{i}{1});
        if ~isempty(tokens{i}{2})
            widths(i) = str2double(tokens{i}{2}(3:end-1));
        end
    end
end
