# scanimage-caiman-two-photon

Raw ScanImage TIFF series and CaImAn outputs for them. ScanImage logs `<base>_<acquisition 5 digits>_<file 5 digits>.tif`, the file counter incrementing when one acquisition is split across files, into a folder the operator chose (here `<yyyy-mm-dd>/<subject>/`). CaImAn writes, per acquisition, `memmap__d1_<h>_d2_<w>_d3_<z>_order_C_frames_<n>_.mmap`, the motion-correction map `<base>_<acq>_rig__d1_…_order_F_frames_<n>_.mmap`, and a results `.hdf5`. Provenance: the ScanImage documentation of file naming and the CaImAn memory-mapping code (`mmapping.py`); see `docs/validation/foreign-datasets.md`.

What it checks:

- Cross-location matching between a file-level entity (the TIFF series) and a folder-level entity (the CaImAn folder) with a three-field composite identity, one field of which (`acquisition_date`) is read from a structural level above.
- Two environments in one location; the listing names `analysis-mac` and both roots are `nas`.
- `cardinality: many` on the TIFF series; `derivedFrom` and `access: readwrite` on the processed location.
- `acquisition_number` kept as a zero-padded string because a token cannot be formatted (gap **G9**): as an integer, `{acquisition_number}` would substitute `1` into a pattern that must match `00001`.
- **Gap G3 (one entity, several folders by design):** subject `m0123` has a folder under each date, so the reader reports `duplicate-entity` on it. A structural level above an entity level makes recurrence normal, not an error.
- **Gap G10 (metadata in member file names):** the frame count and image size in the `.mmap` name cannot be extracted, because rules read path components of the entity, not the names of files matched by `filePatterns`.
- `notes.txt` beside the TIFFs and `calibration/` (not a subject) are `no-match`.
