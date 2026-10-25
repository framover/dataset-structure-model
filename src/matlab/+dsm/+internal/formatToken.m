function text = formatToken(value, width)
%formatToken The text a token substitutes: the value as is, or zero-filled to width digits for a {name:0Nd} format
%
%   A value that is not an integer is substituted as plain text. The
%   validators keep formats off non-integer fields, so this only happens
%   through a value that bypassed them, such as a mistyped defaultValue.
    if isnan(width)
        text = string(value);
        return
    end
    number = value;
    if ischar(value) || isstring(value)
        number = str2double(value);
    end
    isInteger = isnumeric(number) && isscalar(number) && isfinite(number) && (mod(number, 1) == 0);
    if ~isInteger
        text = string(value);
        return
    end
    text = string(sprintf("%0" + string(width) + "d", number));
end
