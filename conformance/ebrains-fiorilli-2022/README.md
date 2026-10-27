# ebrains-fiorilli-2022

An EBRAINS dataset published as a Data Proxy bucket (dataset version `d406a98c-ae5c-4fb3-9f0c-4cf4de9b1094`, Fiorilli et al., tetrode recordings during a visual, tactile and visuotactile discrimination task in the rat). The bucket holds one folder, `hbp-data-002061/`, with the data descriptor, the licence, `code/` and `data/`. Every session file sits flat in `data/`: `neo_<animal>_<yymmdd>.pkl` (spikes, pickled Neo objects) and, for 19 of the 25 sessions, an LFP file `neo_<animal>_<yymmdd>_lfps.nio`. `data/sessions_df.csv` lists the sessions with the columns `animal` and `date`, indexed by `<animal>_<yymmdd>`.

Provenance: the listing is the complete object listing of the public bucket (58 objects, all kept), fetched from the Data Proxy API. Entity names, the file name template `neo_ANIMALID_SESSIONID.pkl` and the file descriptions come from the data descriptor in the bucket (`EBRAINS-DataDescriptor_ViTa-V3.pdf`); the session key comes from `sessions_df.csv`. See `docs/validation/foreign-datasets.md`.

What it checks:

- Two fixed levels (`hbp-data-002061`, `data`) above a `file` level.
- Session identity `<animal>_<yymmdd>`, subject and a two-digit-year date read from one file name by three `regex` rules; four subjects inferred from their sessions, each with `locations: []`.
- A required kind (`spikes`) beside two optional kinds. One session has `_lfps_clean.nio` instead of `_lfps.nio`, a suffix the data descriptor does not mention; it is a kind of its own (`lfp_clean`) rather than folded into `lfp`.
- The 25 session records equal the 25 rows of `sessions_df.csv` in key, animal and date, and the sessions per subject equal Table 1 of the data descriptor (7, 10, 4, 4).
- The data descriptor, the licence, `code/` and `data/sessions_df.csv` are parts of the dataset that belong to no entity; all four are `no-match` (gap **G1**).
- The root path in the config is a placeholder: a published dataset has no file system path that holds for its users (gap **G17**).
