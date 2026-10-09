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

        function outerEntityFilePatternsClaimFilesBeforeTheNextLevel(testCase)
            doc = minimalConfigDoc();
            source = doc.dataLocations.filesystemSource;
            layout = num2cell(source.entityLayout');
            layout{1}.filePatterns = {struct("name", "notes", "pattern", '^notes\.txt$'), ...
                                      struct("name", "log", "pattern", '^{subject_id}_log\.txt$')};
            % a file level below whose pattern and identity rule would also accept the subject's files
            layout{2} = struct("name", "sessions", "entityType", "session", "fileSystemType", "file", "matchPattern", '\.txt$');
            source.entityLayout = layout;
            source.metadataMapping(2).extraction.pattern = '^(.+)\.txt$';
            doc.dataLocations.filesystemSource = source;
            result = walkEntries(doc, {'m110/', 'm110/20250523_a.txt', 'm110/m110_log.txt', 'm110/notes.txt', 'm110/readme.md'});
            subject = result.Records{cellfun(@(r) r.entityType == "subject", result.Records)};
            testCase.verifyEqual(string(subject.locations{1}.files("notes")), "m110/notes.txt");
            testCase.verifyEqual(string(subject.locations{1}.files("log")), "m110/m110_log.txt");
            % the claimed files are neither sessions nor unmatched; the unclaimed file is still no-match
            sessions = result.Records(cellfun(@(r) r.entityType == "session", result.Records));
            testCase.verifyEqual(cellfun(@(r) r.identity.session_id, sessions), "20250523_a");
            testCase.verifyEqual(cellfun(@(u) u.path, result.Unmatched), "m110/readme.md");
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
    end
end

function result = walkEntries(doc, entries)
    result = dsm.walk(dsm.Config(doc), dsm.Listing({dsm.Listing.makeRoot("raw", "main", entries)}));
end
