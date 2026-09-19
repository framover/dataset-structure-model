# ebrains-blackstad-2024

A recent EBRAINS dataset in a bucket named by its dataset version (`40faae41-7e72-4c3c-9abf-91dea149158d`, Blackstad et al., electrophysiological recordings of hippocampal CA1 units in rats during open field foraging). Layout per the data descriptor: `data/<Subject>/<Session_date>/` with Neuralynx files for one rat and Axona files for the other four, plus MClust outputs in both.

Provenance: the object listing of the public bucket, 7,545 entries (7,423 files). The committed listing keeps every folder and the first file of each name shape (digit runs collapsed) per folder: 1,438 entries. The full listing walks to the same 5 subjects and 114 sessions without issues, and every session file but one (`data/24116/2018-04-05/2018-04-05_1_01.jpg`) is named by a file pattern. Meanings are quoted from `data-descriptor_91dea149158d.pdf`. See `docs/validation/foreign-datasets.md`.

What it checks:

- Twelve named file kinds on one session level, several with `{session_id}` tokens (`^{session_id}\.\d$` for Axona tetrode files).
- Two recording systems in one location. The descriptor says rat 24101 was recorded with Neuralynx (`TT<N>.ntt`, `CSC<N>.ncs`, `VT1.nvt`) and the others with Axona (`<date>.<N>`, `<date>.set`, `<date>.pos`). A `.set` file is required in an Axona session and a `.nvt` file in a Neuralynx session, but a file pattern is required in every entity of the level or in none, and the system shows in no name. So no pattern is required (gap **G20**). The full walk shows what the requirement would check: 21 Neuralynx sessions and 93 Axona sessions each have the files of their system; 1 Axona session has no MClust output, and 1 Neuralynx session (`24101/2018-04-18`) names its cluster files `1804201801_8_<NN>.t64` instead of `TT8_<NN>.t64` and has no feature files.
- OptiTrack files in 78 of the 93 Axona sessions, one of them named `2019-05-09_Take 2019-05-09 02.52.05 PM.csv` where the descriptor says `<date>.csv`.
- The data descriptor, the licence, `docs/` and `scripts/` are `no-match` (gap **G1**).
