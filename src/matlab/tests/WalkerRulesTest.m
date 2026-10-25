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

        function duplicateEntityNeedsTheSameParentFolder(testCase)
            doc = minimalConfigDoc();
            source = doc.dataLocations.filesystemSource;
            layout = num2cell(source.entityLayout');
            layout{1}.matchPattern = '^m\d{3}(_copy)?$';
            % a structural date level above the subject: one subject folder per date is the layout's design
            layout = [{struct("name", "dates", "matchPattern", '^\d{8}$')}, layout];
            source.entityLayout = layout;
            source.metadataMapping(1).extraction.pattern = '0:4';
            doc.dataLocations.filesystemSource = source;
            result = walkEntries(doc, {'20250101/', '20250101/m110/', '20250102/', '20250102/m110/', '20250102/m110_copy/'});
            subject = result.Records{cellfun(@(r) r.entityType == "subject", result.Records)};
            testCase.verifyEqual(sort(string(subject.locations{1}.paths)), ["20250101/m110/", "20250102/m110/", "20250102/m110_copy/"]);
            % the folder under a different date is not a duplicate; the _copy beside its original is
            testCase.verifyEqual(cellfun(@(i) i.code, subject.issues), "duplicate-entity");
            testCase.verifyTrue(contains(subject.issues{1}.message, "20250102/"));
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

        function structuralFolderWithNothingMatchingBelowIsUnmatchedItself(testCase)
            doc = minimalConfigDoc();
            layout = num2cell(doc.dataLocations.filesystemSource.entityLayout');
            layout = [layout(1), {struct("name", "years", "matchPattern", "^\d{4}$")}, layout(2)];
            doc.dataLocations.filesystemSource.entityLayout = layout;
            result = walkEntries(doc, {'m110/', 'm110/2025/', 'm110/2025/20250523_a/', ...
                'm110/2024/', ...                            % empty
                'm110/2023/', 'm110/2023/notes.txt', ...     % holds only an entry the next level rejects
                'm110/2022/', 'm110/2022/20220101_b/', 'm110/2022/x.txt'});  % holds an entity: only x.txt is reported
            testCase.verifyEqual(cellfun(@(u) u.path, result.Unmatched), ["m110/2022/x.txt", "m110/2023/", "m110/2024/"]);
            testCase.verifyEqual(cellfun(@(u) u.reason, result.Unmatched), repmat("no-match", 1, 3));
            sessions = result.Records(cellfun(@(r) r.entityType == "session", result.Records));
            testCase.verifyEqual(sort(cellfun(@(r) r.identity.session_id, sessions)), ["a", "b"]);
        function minAndMaxCountBoundTheMatchedFiles(testCase)
            doc = minimalConfigDoc();
            layout = num2cell(doc.dataLocations.filesystemSource.entityLayout');
            layout{2}.filePatterns = {struct("name", "planes", "pattern", "^plane\d\.tif$", "minCount", 2, "maxCount", 2)};
            doc.dataLocations.filesystemSource.entityLayout = layout;
            result = walkEntries(doc, {'m110/', 'm110/20250523_a/', 'm110/20250523_a/plane1.tif', ...
                'm110/20250523_b/', 'm110/20250523_b/plane1.tif', 'm110/20250523_b/plane2.tif', ...
                'm110/20250523_c/', 'm110/20250523_c/plane1.tif', 'm110/20250523_c/plane2.tif', 'm110/20250523_c/plane3.tif'});
            sessions = result.Records(cellfun(@(r) r.entityType == "session", result.Records));
            byId = containers.Map(cellfun(@(r) char(r.identity.session_id), sessions, "UniformOutput", false), sessions);
            testCase.verifyEqual(cellfun(@(i) i.code, byId('a').issues), "missing-required-file");
            testCase.verifyFalse(byId('a').locations{1}.isComplete);
            testCase.verifyEmpty(byId('b').issues);
            testCase.verifyTrue(byId('b').locations{1}.isComplete);
            testCase.verifyEqual(cellfun(@(i) i.code, byId('c').issues), "cardinality-violation");
            testCase.verifyTrue(byId('c').locations{1}.isComplete);
            testCase.verifyEqual(numel(byId('c').locations{1}.files('planes')), 3);
        end
    end
end

function result = walkEntries(doc, entries)
    result = dsm.walk(dsm.Config(doc), dsm.Listing({dsm.Listing.makeRoot("raw", "main", entries)}));
end
