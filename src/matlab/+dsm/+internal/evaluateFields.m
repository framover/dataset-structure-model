function [values, unresolved] = evaluateFields(config, locId, relPath, entityType, seed, registry, fullPath)
%evaluateFields Evaluate every rule for fields of entityType in one location on one path
%
%   values is a struct mapping each mapped field to its value, or [] when
%   the rule produced nothing. unresolved lists registry keys of function
%   rules with no implementation. Ancestor identity comes in through seed.
%
%   Several rules for one field are an ordered fallback. In every pass over
%   the pending rules a rule is evaluated only when it is the first remaining
%   rule for its field and, for a template, no other field it references still
%   has a remaining rule. The first rule that yields a value wins and the
%   field's later rules are dropped unevaluated; a deferred template blocks
%   the later rules for its field until it has run.

    levelNames = config.levelNames(locId);
    definitions = config.definitions();
    rules = config.rulesFor(locId, entityType);
    values = struct();
    known = seed;
    unresolved = string.empty(1, 0);
    pending = rules;
    while ~isempty(pending)
        progressed = false;
        snapshot = pending;
        for i = 1:numel(snapshot)
            item = snapshot{i};
            ref = string(item.metadataRef);
            rule = item.extraction;
            pendingRefs = refsOf(pending);
            position = find(cellfun(@(p) isequal(p, item), pending), 1);
            if isempty(position) || position ~= find(pendingRefs == ref, 1)
                continue  % dropped by an earlier winner, or an earlier rule for this field is still deferred
            end
            if string(rule.method) == "template"
                tokens = templateTokens(rule.pattern);
                if any(ismember(tokens, pendingRefs) & tokens ~= ref)
                    continue
                end
            end
            [value, unresolvedKey] = evaluateRule(rule, definitions.(ref), levelNames, relPath, known, ...
                registry, fullPath, locId);
            pending(position) = [];
            if ~isfield(values, ref) || dsm.internal.isNone(values.(ref))
                values.(ref) = value;
                if ~dsm.internal.isNone(value)
                    known.(ref) = value;
                    pending = pending(refsOf(pending) ~= ref);
                end
            end
            if unresolvedKey ~= ""
                unresolved(end+1) = unresolvedKey; %#ok<AGROW>
            end
            progressed = true;
        end
        if ~progressed
            % a dependency cycle; validation rejects these, so this is defensive
            for i = 1:numel(pending)
                ref = pending{i}.metadataRef;
                if ~isfield(values, ref)
                    values.(ref) = [];
                end
            end
            break
        end
    end
end

function refs = refsOf(items)
    refs = reshape(string(cellfun(@(item) item.metadataRef, items, "UniformOutput", false)), 1, []);
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
            [tokens, literals] = regexp(char(rule.pattern), "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens", "split");
            raw = string(literals{1});
            for i = 1:numel(tokens)
                key = tokens{i}{1};
                if ~isfield(known, key)
                    value = [];
                    return
                end
                raw = raw + string(known.(key)) + string(literals{i+1});
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
    found = regexp(char(text), "\{([A-Za-z_][A-Za-z0-9_]*)\}", "tokens");
    tokens = reshape(string(cellfun(@(t) t{1}, found, "UniformOutput", false)), 1, []);
end
