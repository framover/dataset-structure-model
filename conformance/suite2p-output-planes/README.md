# suite2p-output-planes

A suite2p output folder per session: `<session>/suite2p/plane<N>/` with `F.npy`, `Fneu.npy`, `spks.npy`, `stat.npy`, `ops.npy`, `iscell.npy` and the intermediate `data.bin`; `suite2p/combined/` repeating the per-plane files in the combined view of multi-plane recordings; `suite2p/ops1.npy` at the top of the suite2p folder. Provenance: the suite2p output documentation; see `docs/validation/foreign-datasets.md`.

What it checks:

- A fixed structural level (`suite2p`) between two entity levels, and `excludePatterns` removing `combined/` (reason `excluded`).
- Seven fixed-name file kinds; `m0124_20240316/plane0` lacks the required `stat.npy` → `missing-required-file`.
- Subject inferred from the session folder name; `plane_index` as an integer via `pathComponentTemplate` plus an explicit `matchPattern`.
- **Gap G7 (files inside a structural level):** `ops1.npy` and `run.log` sit in the structural `suite2p/` folder. They belong to the session, but a structural level has no owner to attach files to, so they are `no-match`.
