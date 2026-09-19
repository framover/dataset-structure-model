# ibl-alf-session-path

The International Brain Laboratory ONE/ALF layout: the session path `<lab>/Subjects/<subject>/<yyyy-mm-dd>/<NNN>/`, then collections `alf/`, `raw_ephys_data/`, `raw_video_data/`, `raw_behavior_data/`; per probe a folder `probeNN/` under both `alf/` (spike sorting output, `spikes.times.npy`, …) and `raw_ephys_data/` (SpikeGLX files). ALF file names are `[_namespace_]object.attribute[.extra].extension`. Provenance: the ALF specification in the ONE documentation ("`cortexlab/Subjects/mouse_001/2021-05-27/1/alf/probe00/spikes.times.npy`"); see `docs/validation/foreign-datasets.md`.

What it checks:

- A fixed level (`Subjects`) between two entity levels; a lab entity above the subject.
- Composite session identity `[session_date, session_number]` where the date comes from the structural `dates` level above the session's own level.
- `session_path` read from the whole relative path (`entityLayoutLevel: null`).
- Two sessions on one day (`001`, `002`) are distinct.
- **Gap G3 (one entity, several folders by design):** `probe00` has a folder under `alf/` and another under `raw_ephys_data/`. The structural `collections` level makes both folders resolve to the same probe, which is what the dataset means, but the reader reports `duplicate-entity` because two folders in one location yielded one identity. The fixture pins this as current behaviour.
- **Gap G5 (branching):** `alf/_ibl_trials.*.npy` (files where the next level expects probe folders), the nidq files in `raw_ephys_data/`, `raw_video_data/` and `raw_behavior_data/` all belong to the session but are `no-match`, because a location has one linear layout.
