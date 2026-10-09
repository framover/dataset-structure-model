function [atLeast, atMost] = countBounds(pattern)
%countBounds Smallest and largest number of files a fileGroupingPattern expects per entity
%
%   [atLeast, atMost] = countBounds(pattern) returns atMost = Inf when the
%   count is unbounded. isRequired means at least one and cardinality 'one'
%   means at most one; minCount and maxCount say any bound. Validation
%   refuses a pattern whose two spellings disagree, so either may be read.

    import dsm.internal.getField
    if isfield(pattern, "minCount")
        atLeast = double(pattern.minCount);
    elseif getField(pattern, "isRequired", false)
        atLeast = 1;
    else
        atLeast = 0;
    end
    if isfield(pattern, "maxCount")
        atMost = double(pattern.maxCount);
    elseif string(getField(pattern, "cardinality", "many")) == "one"
        atMost = 1;
    else
        atMost = Inf;
    end
end
