function [values, unresolved] = evaluateFields(config, locId, relPath, entityType, seed, registry, fullPath)
%evaluateFields Evaluate every rule for fields of entityType in one location on one path
%
%   values is a struct mapping each mapped field to its value, or [] when
%   the rule produced nothing. unresolved lists registry keys of function
%   rules with no implementation. Templates are evaluated after the own-type
%   fields they reference; ancestor identity comes in through seed.

    levelNames = config.levelNames(locId);
    definitions = config.definitions();
    rules = config.rulesFor(locId, entityType);
    values = struct();
    known = seed;
    unresolved = string.empty(1, 0);
    pending = rules;
    pendingRefs = string(cellfun(@(item) item.metadataRef, rules, "UniformOutput", false));
    while ~isempty(pending)
        progressed = false;
        for i = numel(pending):-1:1
            ref = string(pending{i}.metadataRef);
            rule = pending{i}.extraction;
            if string(rule.method) == "template"
                tokens = templateTokens(rule.pattern);
                waiting = tokens(ismember(tokens, pendingRefs) & tokens ~= ref);
                if ~isempty(waiting)
                    continue
                end
            end
            [value, unresolvedKey] = evaluateRule(rule, definitions.(ref), levelNames, relPath, known, registry, fullPath, locId);
            values.(ref) = value;
            if ~dsm.internal.isNone(value)
                known.(ref) = value;
            end
            if unresolvedKey ~= ""
                unresolved(end+1) = unresolvedKey; %#ok<AGROW>
            end
            pending(i) = [];
            pendingRefs(pendingRefs == ref) = [];
            progressed = true;
        end
        if ~progressed
            % a dependency cycle; validation rejects these, so this is defensive
            for i = 1:numel(pending)
                values.(pending{i}.metadataRef) = [];
            end
            break
        end
    end
end

function [value, unresolvedKey] = evaluateRule(rule, definition, levelNames, relPath, known, registry, fullPath, locId)
    unresolvedKey = "";
    method = string(rule.method);
    switch method
        case "fixed"
            value = dsm.internal.coerceValue(rule.value, definition, rule);
            return
        case "function"
            key = string(rule.extractorFunction);
            fcn = registry.get(key);
            if isempty(fcn)
                unresolvedKey = key;
                value = [];
                return
            end
            raw = fcn(fullPath, dsm.internal.levelNameFor(rule, levelNames), string(locId));
            if dsm.internal.isNone(raw)
                value = [];
            else
                value = dsm.internal.coerceValue(raw, definition, rule);
            end
            return
        case "template"
            [names, widths, literals] = dsm.internal.tokenParts(rule.pattern);
            raw = string(literals{1});
            for i = 1:numel(names)
                if ~isfield(known, names(i))
                    value = [];
                    return
                end
                raw = raw + dsm.internal.formatToken(known.(names(i)), widths(i)) + string(literals{i+1});
            end
        case "sidecar"
            % DRAFT: not implemented by this reader
            unresolvedKey = "sidecar";
            value = [];
            return
        otherwise
            component = dsm.internal.componentFor(rule, levelNames, relPath);
            if isempty(component)
                value = [];
                return
            end
            if method == "substring"
                raw = dsm.internal.applySlice(component, rule.pattern);
            else
                if isempty(regexp(char(component), rule.pattern, "once"))
                    value = [];
                    return
                end
                tokens = regexp(char(component), rule.pattern, "tokens", "once");
                if isempty(tokens)
                    raw = string(regexp(char(component), rule.pattern, "match", "once"));
                else
                    raw = string(tokens{1});
                end
            end
    end
    raw = dsm.internal.normalizeValue(raw, rule);
    value = dsm.internal.coerceValue(raw, definition, rule);
end

function tokens = templateTokens(text)
    tokens = dsm.internal.tokenParts(text);
end
