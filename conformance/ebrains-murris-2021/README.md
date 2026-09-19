# ebrains-murris-2021

An EBRAINS dataset organised as a paper supplement (dataset version `87a63af5-06ac-4fec-89e0-b7f1a9d6c192`, Murris et al., VTA-induced plasticity of visual cortex in macaque monkeys). The file repository in the Knowledge Graph is `p22717-hbp-d000058_VTAinducedVPLandPlasticity_pub?prefix=v1.0`. Of its 5,138 files, 1,044 are raw fMRI and per-session behaviour; the rest are analysis outputs, stimulus images and scripts grouped by figure (`scripts_storage/Figure1D_sigmoidcurves/`, `FigureS1_visual_stimuli/Faces/`, …), with no entity in their paths.

Provenance: the object listing of the public bucket below four roots inside `v1.0/` (1,156 entries). The committed listing keeps every folder, runs 1 to 3 of each scanning day, and all behaviour files (511 entries); the full listing walks to 2 monkeys, 26 scanning days, 293 runs and 69 behaviour sessions with the same issues and the same 52 unmatched folders. The dataset has no overall data descriptor; there are README files per analysis folder. See `docs/validation/foreign-datasets.md`.

What it checks:

- The branching workaround of gap **G5** on a tree where most branches hold no entities: four data locations rooted at `fMRI_VTA-EM_association/raw`, `fMRI_localizer/raw`, `behaviour_colour_task/data_all_sessions` and `behaviour_colour_task/fMRI_runs_data`. Everything else in `v1.0/` is outside every root.
- A composite session identity (experiment, day) where the experiment comes from a structural level above the subject (`PRE_stim`, `POST_stim`) in one location and from a `fixed` rule (`localizer`) in another, because day numbers restart in each experiment.
- A file-level run entity below a fixed `funct` level, with the NIfTI series and its JSON sidecar as one run.
- Each behaviour session is one record found in both behaviour folders, and each monkey is one record found in both fMRI locations and inferred from the behaviour file names.
- `duplicate-entity` on both monkeys, because `m1/` and `m2/` each sit under `PRE_stim/` and `POST_stim/` (gap **G3**).
- A scanning day holds `funct/`, `timing/` and `struct/`. The run's SPM timing file is in `timing/` (`m1_d1_run_SPM_1.mat`, or `m1_d1_SPM_1.mat` in the localizer) and the day's anatomical scan in `struct/` (`m1_d1_gre.nii`). Neither can be described next to the runs, so both folders are `no-match`:
  - With a structural level `^(funct|timing|struct)$` instead of the fixed `funct` level, the Python reader makes one record of run 1 from `funct/m1_d1_run_1.nii.gz`, `funct/m1_d1_run_1.json` and `timing/m1_d1_run_SPM_1.mat`. The self-consistency suite instead expects a file entity's paths to be files of one folder (gap **G21**).
  - With that structural level, the `struct/` folder matches the level but nothing below it matches the run level. The reader reports the scans inside it as `no-match`; the self-consistency suite expects the folder itself to be either covered or unmatched (gap **G22**). The scans belong to the scanning day, which is gap **G6**.
- The behaviour session identity is the whole file stem (`m1_20180625`) rather than the date, which would be unique only within a monkey. The self-consistency suite compares a file entity's own identity without the monkey inferred from the same file name, so a date-only identity fails it although the reader scopes the identity by the monkey correctly.
