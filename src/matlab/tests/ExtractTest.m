classdef ExtractTest < matlab.unittest.TestCase
%ExtractTest The extraction contract: slices, LDML formats, normalize, typing, validation

    properties (TestParameter)
        slice = {{"0:4", "m110"}, {"5:13", "20250510"}, {":-4", "m110-20250510-001_raw"}, ...
                 {":", "m110-20250510-001_raw.tif"}, {"-3:", "tif"}, {"9:", "0510-001_raw.tif"}, {"20:5", ""}}
        temporal = {{"yyyyMMdd", "20250523", "date", "2025-05-23"}, ...
                    {"yyyy_MM_dd", "2025_05_23", "date", "2025-05-23"}, ...
                    {"HH_mm_ss", "10_00_00", "time", "10:00:00"}, ...
                    {"yyyy-MM-dd'T'HHmmss", "2025-05-23T100000", "datetime", "2025-05-23T10:00:00"}, ...
                    {"yyMMdd", "170518", "date", "2017-05-18"}, ...
                    {"yyMMdd", "690518", "date", "1969-05-18"}, ...  % two-digit years: 1969-2068, as strptime
                    {"yyMMdd", "680518", "date", "2068-05-18"}}
    end

    methods (Test)
        function slicesArePythonSlices(testCase, slice)
            testCase.verifyEqual(dsm.internal.applySlice("m110-20250510-001_raw.tif", slice{1}), string(slice{2}));
        end

        function ldmlFormatsParseToIso(testCase, temporal)
            definition = struct("dataType", temporal{3});
            rule = struct("valueFormat", temporal{1});
            testCase.verifyEqual(dsm.internal.coerceValue(temporal{2}, definition, rule), string(temporal{4}));
        end

        function unparsableTemporalIsNone(testCase)
            value = dsm.internal.coerceValue("not-a-date", struct("dataType", "date"), struct("valueFormat", "yyyyMMdd"));
            testCase.verifyTrue(dsm.internal.isNone(value));
        end

        function normalizeModes(testCase)
            testCase.verifyEqual(dsm.internal.normalizeValue("sub-m110", struct("normalize", "strip_prefix", "normalizePattern", "sub-")), "m110");
            testCase.verifyEqual(dsm.internal.normalizeValue("m110.raw", struct("normalize", "strip_suffix", "normalizePattern", ".raw")), "m110");
            testCase.verifyEqual(dsm.internal.normalizeValue("  AB ", struct("normalize", "trim")), "AB");
            testCase.verifyEqual(dsm.internal.normalizeValue("AB", struct("normalize", "lowercase")), "ab");
            testCase.verifyEqual(dsm.internal.normalizeValue("ab", struct()), "ab");
        end

        function integerTyping(testCase)
            testCase.verifyEqual(dsm.internal.coerceValue("7", struct("dataType", "integer"), struct()), 7);
            testCase.verifyTrue(dsm.internal.isNone(dsm.internal.coerceValue("7.5", struct("dataType", "integer"), struct())));
            testCase.verifyTrue(dsm.internal.isNone(dsm.internal.coerceValue("x", struct("dataType", "number"), struct())));
        end

        function validationProblems(testCase)
            definition = struct("dataType", "string", "validation", struct("pattern", "^m\d{3}$"));
            testCase.verifyEqual(dsm.internal.validateValue("m110", definition), "");
            testCase.verifyNotEqual(dsm.internal.validateValue("x110", definition), "");
            numeric = struct("dataType", "number", "validation", struct("minimum", 0, "maximum", 10));
            testCase.verifyNotEqual(dsm.internal.validateValue(11, numeric), "");
        end

        function templateDerivesMatchPattern(testCase)
            config = dsm.Config(minimalConfigDoc());
            doc = config.Document;
            doc.metadataDefinitions.session_id.validation = struct("pattern", "^m\d{3}-\d{8}-\d{3}$");
            config = dsm.Config(doc);
            level = struct("name", "sessions", "entityType", "session", "pathComponentTemplate", "session-{session_id}");
            testCase.verifyTrue(config.nameMatches(level, "session-m110-20250523-001"));
            testCase.verifyFalse(config.nameMatches(level, "scratch"));
            testCase.verifyFalse(config.nameMatches(level, "session-m110-20250523-0011"));
        end

        function tokenFormatZeroFillsIntegers(testCase)
            testCase.verifyEqual(dsm.internal.formatToken(7, 5), "00007");
            testCase.verifyEqual(dsm.internal.formatToken("7", 3), "007");
            testCase.verifyEqual(dsm.internal.formatToken(123456, 5), "123456");  % wider values keep their digits
            testCase.verifyEqual(dsm.internal.formatToken(7, NaN), "7");
            testCase.verifyEqual(dsm.internal.formatToken("00007", NaN), "00007");
            [names, widths, literals] = dsm.internal.tokenParts("a{x}_{y:05d}");
            testCase.verifyEqual(names, ["x", "y"]);
            testCase.verifyEqual(widths, [NaN, 5]);
            testCase.verifyEqual(literals, {'a', '_', ''});
        end

        function tokenFormatDerivesADigitPattern(testCase)
            doc = minimalConfigDoc();
            doc.metadataDefinitions.session_id.dataType = "integer";
            config = dsm.Config(doc);
            level = struct("name", "sessions", "entityType", "session", "pathComponentTemplate", "run-{session_id:03d}");
            testCase.verifyTrue(endsWith(config.matchRegex(level), '\d{3,}$'), config.matchRegex(level));
            testCase.verifyTrue(config.nameMatches(level, "run-007"));
            testCase.verifyFalse(config.nameMatches(level, "run-7"));
        end
    end
end
