# deeplabcut-project

A DeepLabCut project `<Task>-<Experimenter>-<yyyy-mm-dd>/` with `config.yaml` and the folders `videos/`, `labeled-data/`, `training-datasets/`, `dlc-models/`. `videos/` holds the source videos and, after analysis, `<video>DLC_<model>shuffle<N>_<iteration>.h5/.csv`, `…_meta.pickle` and `…_labeled.mp4` beside them. `labeled-data/<video>/` holds the extracted frames `img<NNN>.png` and the labels `CollectedData_<scorer>.csv/.h5`; `labeled-data/<video>_labeled/` holds the check-labels output. Provenance: the DeepLabCut user guide; see `docs/validation/foreign-datasets.md`.

What it checks:

- **The workaround for gap G5 (branching):** one physical project tree described as two data locations rooted at `videos/` and `labeled-data/`, so the video entity is a file group in one and a folder in the other, matched by `video_name`.
- A file-level identity rule that must cover two naming forms with one regex (`<video>.avi` and `<video>DLC_…`), because a field has one rule per location (gap **G8**).
- `cardinality: many` outputs from several trained models (`reachingvideo3` has two iterations); a video with no analysis yet (`reachingvideo2`) is still complete.
- `excludePatterns` on `_labeled$` folders (reason `excluded`).
- `config.yaml`, `training-datasets/` and `dlc-models/` are outside both roots and cannot be described without a third location.
