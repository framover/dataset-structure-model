# open-ephys-binary

The Open Ephys GUI binary format: `Record Node <id>/experiment<N>/recording<M>/` with `continuous/<stream>/continuous.dat`, `timestamps.npy`, `sample_numbers.npy`; `events/<stream>/TTL/` with `states.npy`, `sample_numbers.npy`, `timestamps.npy`, `full_words.npy`; `events/MessageCenter/`; `spikes/`; `structure.oebin` and `sync_messages.txt` in the recording folder; `settings.xml` in the Record Node folder. Stream folders are named `<processor>-<id>.<stream>`. Provenance: the Open Ephys GUI documentation of the binary format; see `docs/validation/foreign-datasets.md`.

What it checks:

- Four entity levels with a fixed structural level (`continuous`) in between; folder names with spaces and dots.
- Integer identities scoped by parents: `recording1` under `Record Node 101/experiment1` and under `Record Node 102/experiment1` are two recordings; stream `Neuropix-PXI-100.ProbeA-AP` recurs under two recordings.
- `processor_id` read out of the stream folder name.
- **Gap G2 (files of an outer entity):** `structure.oebin`, `sync_messages.txt` and `settings.xml` are in their entity's `files` and also `no-match`.
- **Gap G5 (branching):** `events/` and `spikes/` are sibling branches under the recording with their own hierarchy; one linear layout cannot describe both, so they are `no-match`.
