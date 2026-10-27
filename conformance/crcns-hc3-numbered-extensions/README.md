# crcns-hc3-numbered-extensions

The CRCNS hc-3 layout (Buzsáki lab): a top directory per group of recordings with the same electrode placement (`ec013.15`), a folder per session (`ec013.156`), and inside it files that all carry the session name: `.xml` (parameters), `.eeg` (LFP), `.whl` (position), and per electrode group N the four files `.clu.N`, `.res.N`, `.fet.N`, `.spk.N`. `docs/` and `hc3-metadata-tables/` sit beside the data. Provenance: the hc-3 data description on crcns.org and the download portal listing; see `docs/validation/foreign-datasets.md`.

What it checks:

- Four entity types on three levels: the animal (`ec013`) is inferred from the top directory name and has no folder; the recording day and the session are folders; the shank is a file-level entity keyed by the numeric extension (`integer`, so `.clu.10` is shank 10, not a string after shank 1).
- Two ancestors' identity substituted into one pattern: `^{session_id}\.clu\.{shank_number}$`.
- `ec013.157` shank 2 has a `.clu.2` but no `.res.2` → `missing-required-file`.
- **Gap G2 (files of an outer entity):** `ec013.156.xml`, `.eeg` and `.whl` are direct children of the session folder and match the session's `filePatterns`, so they appear in the session's `files`, *and* they are reported `no-match` because the level below expects shank files. The fixture pins this double accounting as the current behaviour; the validation report proposes the fix.
- `docs/` and `hc3-metadata-tables/` are `no-match` (gap **G1**).
