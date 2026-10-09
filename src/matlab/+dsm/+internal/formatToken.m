function text = formatToken(value, width)
%formatToken The text a token substitutes: the value as is, or zero-filled to width digits for a {name:0Nd} format
    if isnan(width)
        text = string(value);
        return
    end
    if ischar(value) || isstring(value)
        value = str2double(value);
    end
    text = string(sprintf("%0" + string(width) + "d", value));
end
