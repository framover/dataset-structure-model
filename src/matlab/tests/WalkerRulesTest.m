classdef WalkerRulesTest < matlab.unittest.TestCase
%WalkerRulesTest Reader rules with no fixture case, on in-memory listings

    methods (Test)
        function metadataConflictBetweenLocations(testCase)
            doc = minimalConfigDoc();
            doc.metadataDefinitions.note = struct("name", "note", "dataType", "string", "ofEntity", "session");
            source = doc.dataLocations.filesystemSource;
            mapping = num2cell(source.metadataMapping');
            mapping{end+1} = struct("metadataRef", "note", "extraction", struct("method", "regex", "pattern", "_(.+)$", "entityLayoutLevel", "sessions"));
            source.metadataMapping = mapping;
            doc.dataLocations.filesystemSource = source;
            second = doc.dataLocations;
            second.identifier = 'copy';
            second.dataCategory = 'processed';
            secondMapping = mapping(1:2);
            secondMapping{end+1} = struct("metadataRef", "note", "extraction", struct("method", "fixed", "value", "other"));
            second.filesystemSource.metadataMapping = secondMapping;
            doc.dataLocations = {doc.dataLocations, second};
            listing = dsm.Listing({dsm.Listing.makeRoot("raw", "main", {'m110/', 'm110/20250523_baseline/'}), ...
                                   dsm.Listing.makeRoot("copy", "main", {'m110/', 'm110/20250523_baseline/'})});
            result = dsm.walk(dsm.Config(doc), listing);
            session = result.Records{cellfun(@(r) r.entityType == "session", result.Records)};
            testCase.verifyEqual(numel(session.locations), 2);
            testCase.verifyEqual(session.metadata.note, "baseline");
            testCase.verifyEqual(cellfun(@(i) i.code, session.issues), "metadata-conflict");
        end

        function validationFailedIsReportedButValueKept(testCase)
            doc = minimalConfigDoc();
            doc.metadataDefinitions.subject_id.validation = struct("pattern", "^m1");
            result = walkEntries(doc, {'m110/', 'm220/'});
            byId = containers.Map(cellfun(@(r) char(r.identity.subject_id), result.Records, "UniformOutput", false), result.Records);
            testCase.verifyEqual(byId('m220').metadata.subject_id, "m220");
            testCase.verifyEqual(cellfun(@(i) i.code, byId('m220').issues), "validation-failed");
            testCase.verifyEmpty(byId('m110').issues);
        end

        function entityWithoutExtractableIdentityIsUnmatched(testCase)
            result = walkEntries(minimalConfigDoc(), {'m110/', 'm110/20250523_/'});
            testCase.verifyEqual(cellfun(@(u) u.path, result.Unmatched), "m110/20250523_/");
            testCase.verifyEqual(cellfun(@(r) r.entityType, result.Records), "subject");
        end

        function structuralInnermostLevelIsCovered(testCase)
            doc = minimalConfigDoc();
            layout = num2cell(doc.dataLocations.filesystemSource.entityLayout');
            layout{end+1} = struct("name", "processed", "isVariable", false, "fixedName", "processed");
            doc.dataLocations.filesystemSource.entityLayout = layout;
            result = walkEntries(doc, {'m110/', 'm110/20250523_baseline/', 'm110/20250523_baseline/processed/', ...
                'm110/20250523_baseline/processed/x.dat', 'm110/20250523_baseline/raw/'});
            testCase.verifyEqual(cellfun(@(u) u.path, result.Unmatched), "m110/20250523_baseline/raw/");
        end

        function recordsAreOrderedByDeclarationThenKey(testCase)
            result = walkEntries(minimalConfigDoc(), {'m220/', 'm220/20250523_b/', 'm110/', 'm110/20250523_a/'});
            labels = cellfun(@(r) r.entityType + ":" + strjoin(string(struct2cell(r.identity))', ","), result.Records);
            testCase.verifyEqual(labels, ["subject:m110", "subject:m220", "session:a", "session:b"]);
        end

        function reportRenders(testCase)
            doc = minimalConfigDoc();
            config = dsm.Config(doc, "memory.json");
            result = dsm.walk(config, dsm.Listing({dsm.Listing.makeRoot("raw", "main", {'m110/', 'm110/20250523_a/', 'temp/'})}));
            text = dsm.renderReport(config, result);
            testCase.verifyTrue(contains(text, "session: 1"));
            testCase.verifyTrue(contains(text, "Unmatched: 1"));
        end

        function rootPathIsOptionalForWalking(testCase)
            doc = minimalConfigDoc();
            doc.dataLocations.filesystemSource.rootStoragePaths = rmfield(doc.dataLocations.filesystemSource.rootStoragePaths, "path");
            entries = {'m110/', 'm110/20250523_a/'};
            result = walkEntries(doc, entries);
            testCase.verifyEqual(cellfun(@(r) r.entityType, result.Records), ["subject", "session"]);
            testCase.verifyEmpty(result.Warnings);
            % only a function extractor sees a real path: without one the walk warns once and passes the relative path
            doc.metadataDefinitions.note = struct("name", "note", "dataType", "string", "ofEntity", "session");
            mapping = num2cell(doc.dataLocations.filesystemSource.metadataMapping');
            mapping{end+1} = struct("metadataRef", "note", "extraction", struct("method", "function", "extractorFunction", "path_as_note"));
            doc.dataLocations.filesystemSource.metadataMapping = mapping;
            registry = dsm.ExtractorRegistry(struct("path_as_note", @(fullPath, levelName, locId) string(fullPath)));
            result = dsm.walk(dsm.Config(doc), dsm.Listing({dsm.Listing.makeRoot("raw", "main", entries)}), registry);
            testCase.verifyEqual(result.Records{2}.metadata.note, "m110/20250523_a");
            testCase.verifyEqual(numel(result.Warnings), 1);
            testCase.verifyTrue(contains(result.Warnings, "raw/main has no path"));
        end
    end
end

function result = walkEntries(doc, entries)
    result = dsm.walk(dsm.Config(doc), dsm.Listing({dsm.Listing.makeRoot("raw", "main", entries)}));
end
