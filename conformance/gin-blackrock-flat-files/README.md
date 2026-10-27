# gin-blackrock-flat-files

A GIN repository with recordings as flat files (layout of `INT/multielectrode_grasp`, doi:10.12751/g-node.f83565): `datasets/` holds, per session `<monkey letter><yymmdd>-<nnn>`, the Blackrock files `.nev`, `.ns2`, `.ns5`/`.ns6`, `.ccf`, an odML metadata file, and a second `.nev` with a two-digit suffix for the offline-sorted spikes. `code/`, `datasets_matlab/`, `README.md` and `LICENSE.txt` are siblings. Provenance: the repository's file listing and the data descriptor (Brochier et al. 2018); see `docs/validation/foreign-datasets.md`.

What it checks:

- A fixed structural level (`datasets`) above a `file` level.
- Subject inferred from the first character of the session name (`substring 0:1`), with an `enum` validation; both subjects get `locations: []`.
- A two-digit year in the session name (`yyMMdd` → 2014-07-03, 2010-12-10).
- Seven file kinds per session, with `isRequired` on `.nev` and `.odml`; `ns5` is absent for one monkey and present for the other, without an issue.
- `datasets_matlab/i140703-001.mat` is the same session in a sibling branch, and nothing in one location can reach it: it is `no-match`. See gap **G5** (branching layouts).
