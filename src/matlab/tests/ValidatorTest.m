classdef ValidatorTest < matlab.unittest.TestCase
%ValidatorTest Schema interpretation and reference integrity

    methods (Test)
        function minimalConfigIsValid(testCase)
            doc = minimalConfigDoc();
            testCase.verifyEmpty(dsm.schemaErrors(doc));
            testCase.verifyEmpty(dsm.referenceProblems(doc));
        end

        function examplesAreValid(testCase)
            examples = dir(fullfile(dsm.internal.repoRoot(), "examples", "*.json"));
            testCase.assertNotEmpty(examples);
            for example = examples'
                doc = dsm.internal.readJson(fullfile(example.folder, example.name));
                testCase.verifyEmpty(dsm.schemaErrors(doc), example.name);
                testCase.verifyEmpty(dsm.referenceProblems(doc), example.name);
            end
        end

        function invalidSchemaCaseIsRejectedForTheRightReasons(testCase)
            doc = dsm.internal.readJson(fullfile(dsm.conformance.casesDirectory(), "invalid-schema", "config.json"));
            errors = dsm.schemaErrors(doc);
            testCase.verifyTrue(any(contains(errors, "isAvailable")), strjoin(errors, newline));
            testCase.verifyTrue(any(contains(errors, "0:end")), strjoin(errors, newline));
        end

        function invalidReferenceCaseIsRejected(testCase)
            doc = dsm.internal.readJson(fullfile(dsm.conformance.casesDirectory(), "invalid-reference", "config.json"));
            testCase.verifyEmpty(dsm.schemaErrors(doc));
            problems = dsm.referenceProblems(doc);
            testCase.verifyTrue(any(contains(problems, "subject_code")));
            testCase.verifyTrue(any(contains(problems, "'nope'")));
            testCase.verifyTrue(any(contains(problems, "ghost")));
        end

        function identityMustBeExactlyOneForm(testCase)
            doc = minimalConfigDoc();
            doc.entityTypes(1).identifierRefs = {"subject_id"};
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
            doc = minimalConfigDoc();
            doc.entityTypes = rmfield(doc.entityTypes, "identifierRef");
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
        end

        function perMethodRequiredFields(testCase)
            doc = minimalConfigDoc();
            doc.dataLocations.filesystemSource.metadataMapping(1).extraction = struct("method", "fixed");
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
            doc.dataLocations.filesystemSource.metadataMapping(1).extraction = struct("method", "fixed", "value", "x");
            testCase.verifyEmpty(dsm.schemaErrors(doc));
            doc.dataLocations.filesystemSource.metadataMapping(1).extraction = struct("method", "function", "extractorFunction", "project.datalocation.getSubjectID");
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
        end

        function levelConstraints(testCase)
            doc = minimalConfigDoc();
            doc.dataLocations.filesystemSource.entityLayout(1) = struct("name", "subjects", "entityType", "subject", "matchPattern", "^m\d{3}$");
            layout = {struct("name", "subjects", "entityType", "subject"), struct("name", "sessions", "entityType", "session", "matchPattern", "^\d{8}_.+$")};
            doc.dataLocations.filesystemSource.entityLayout = layout;
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
            layout{1}.pathComponentTemplate = "{subject_id}";
            doc.dataLocations.filesystemSource.entityLayout = layout;
            testCase.verifyEmpty(dsm.schemaErrors(doc));
            layout{end+1} = struct("name", "processed", "isVariable", false);
            doc.dataLocations.filesystemSource.entityLayout = layout;
            testCase.verifyNotEmpty(dsm.schemaErrors(doc));
        end

        function templateCyclesAndLayoutOrderAreReferenceProblems(testCase)
            doc = minimalConfigDoc();
            doc.metadataDefinitions.a = struct("name", "a", "dataType", "string", "ofEntity", "session");
            doc.metadataDefinitions.b = struct("name", "b", "dataType", "string", "ofEntity", "session");
            mapping = num2cell(doc.dataLocations.filesystemSource.metadataMapping');
            mapping{end+1} = struct("metadataRef", "a", "extraction", struct("method", "template", "pattern", "{b}-x"));
            mapping{end+1} = struct("metadataRef", "b", "extraction", struct("method", "template", "pattern", "{a}-y"));
            doc.dataLocations.filesystemSource.metadataMapping = mapping;
            testCase.verifyTrue(any(contains(dsm.referenceProblems(doc), "template cycle")));

            doc = minimalConfigDoc();
            doc.dataLocations.filesystemSource.entityLayout = flipud(doc.dataLocations.filesystemSource.entityLayout);
            testCase.verifyTrue(any(contains(dsm.referenceProblems(doc), "declaration order")));
        end

        function validateConfigThrowsCodedErrors(testCase)
            doc = minimalConfigDoc();
            doc.dataLocations.filesystemSource.rootStoragePaths.isAvailable = true;
            testCase.verifyError(@() dsm.validateConfig(doc), "dsm:config:schemaValidation");
            doc = minimalConfigDoc();
            doc.entityTypes(1).identifierRef = "missing";
            testCase.verifyError(@() dsm.validateConfig(doc), "dsm:config:referenceIntegrity");
            doc = minimalConfigDoc();
            mapping = num2cell(doc.dataLocations.filesystemSource.metadataMapping');
            mapping{end+1} = struct("metadataRef", "session_id", "extraction", struct("method", "sidecar", "filePattern", "*.json", "contentPath", "id"));
            doc.dataLocations.filesystemSource.metadataMapping = mapping;
            testCase.verifyError(@() dsm.validateConfig(doc), "dsm:config:unsupportedDraft");
            dsm.validateConfig(doc, "RejectDraft", false);
        end

        function levelIsRequiredFalseIsDraft(testCase)
            doc = minimalConfigDoc();
            layout = num2cell(doc.dataLocations.filesystemSource.entityLayout');
            layout{1}.isRequired = false;
            doc.dataLocations.filesystemSource.entityLayout = layout;
            testCase.verifyError(@() dsm.validateConfig(doc), "dsm:config:unsupportedDraft");
            dsm.validateConfig(doc, "RejectDraft", false);
        end

        function localOverlaySuppliesPreferences(testCase)
            folder = testCase.applyFixture(matlab.unittest.fixtures.TemporaryFolderFixture).Folder;
            writeJson(fullfile(folder, "ds.json"), minimalConfigDoc());
            writeJson(fullfile(folder, "ds.local.json"), struct("preferences", struct("defaultDataLocationIdentifier", "raw")));
            config = dsm.loadConfig(fullfile(folder, "ds.json"));
            testCase.verifyEqual(config.preferences().defaultDataLocationIdentifier, 'raw');
        end
    end
end

function writeJson(path, doc)
    fid = fopen(path, "w");
    cleanup = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(doc), "char");
end
