# ebrains-bos-2019

An EBRAINS dataset stored as one folder of a shared bucket (dataset version `2077efac-09f6-47c1-aabe-632e08ed148b`, Bos et al., multi-area recordings from visual and somatosensory cortices, perirhinal cortex and hippocampal CA1). The file repository in the Knowledge Graph is `p25b4e-Pennartz_SGA1_T3.3.3?prefix=hbp-01681/`. Layout: `hbp-01681/TouchAndSee/<animal>/samp<N>/hbp-01681_TouchAndSee_<animal>_samp<N>__<yyyy-MM-dd>.pkl`.

Provenance: the complete object listing of `hbp-01681/` in the public bucket (57 entries; the bucket's 50 empty folder objects are listed as folders). The meaning of each level is from `00-hbp-01681_DataDescriptor_v1p1.pdf`. See `docs/validation/foreign-datasets.md`.

What it checks:

- A session folder that holds exactly one file, with the session date in the file name only. A folder-level session could not read that date, because a rule reads the path components of the entity's own levels, not the names of files inside it (gap **G10**). The config therefore makes `samp<N>/` a structural level and the file the session entity, so the file's name is the entity's own path component.
- Two fixed levels above the animals, and a session number that runs across animals (`samp1`–`samp19` for Taskmaster, `samp20`–`samp33` for Ramachandran, `samp34`–`samp46` for Turing).
- The walk yields 3 subjects and 46 sessions without issues. Three dates have two sessions each (2012-01-03, 2012-08-22, 2012-09-15), so the date is not an identity.
- The data descriptor's registry describes `touch_and_see/data/<Animal_name>/<Session>/session.pkl`, `data/maze_outline.pkl` and `examples/`. The bucket has `TouchAndSee/<animal>/samp<N>/…pkl`, no `maze_outline.pkl` and no `examples/` folder; an example notebook and a script sit directly in `TouchAndSee/`.
- The data descriptor, the licence, `hbp-01681.json` and the two example files are `no-match` (gap **G1**).
