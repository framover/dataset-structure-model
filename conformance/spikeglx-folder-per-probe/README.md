# spikeglx-folder-per-probe

SpikeGLX output with the *folder per probe* option: a run folder `<run>_g<N>` per gate, holding the NI-DAQ files `<run>_g<N>_t<T>.nidq.bin/.meta` for every trigger T and one folder `<run>_g<N>_imec<K>/` per probe with `<run>_g<N>_t<T>.imec<K>.ap.bin/.ap.meta/.lf.bin/.lf.meta`. Provenance: the SpikeGLX user manual and the "Parsing data files" page; see `docs/validation/foreign-datasets.md`.

What it checks:

- Composite gate identity `[run_name, gate_index]` with an integer component; probe identity as an integer scoped by the gate.
- File patterns with tokens from the parent (`{run_name}`, `{gate_index}`) and from the entity itself (`{probe_index}`), and `cardinality: many` for the per-trigger series (gate 1 has `t0` and `t1`).
- A CatGT output `…_tcat.imec0.ap.bin` inside the probe folder matches no pattern; it is covered by the innermost entity and not reported.
- **Files of an outer entity (G2):** the nidq files match the gate's `filePatterns`, so they are in the gate's `files` and are not offered to the probe level. `notes.txt` beside them matches no gate pattern and is `no-match`.
