# Examples

Complete configurations, each validated against the schema by the test suite. The JSON files are in [`examples/`](https://github.com/framover/dataset-structure-model/tree/main/examples).

<div class="grid cards" markdown>

-   :material-file-tree: **Flat Session Files**

    ---

    Every session's files exported into one folder. A `file` level groups them into sessions by identity, with `{session_id}` tokens in the file patterns.

    [:octicons-arrow-right-24: Walkthrough](flat-session-files.md)

-   :material-source-branch: **Raw and Processed Two-Photon**

    ---

    Raw data under `{date}/{session}`, processed data under `{subject}/{session}`: structural levels, cross-location matching, generated folder names, `access` and `uuid`.

    [:octicons-arrow-right-24: Walkthrough](raw-processed-two-photon.md)

-   :material-brain: **SHAREbrain Toy Dataset**

    ---

    Session → recording → trial with a composite session identity and the subject identified from the session folder name.

    [:octicons-arrow-right-24: Walkthrough](sharebrain.md)

</div>

---

Validate any of them:

```bash
python -m jsonschema -i examples/flat_session_files.json schema/DatasetStructureModel.schema.json
```

The [conformance fixtures](../guides/conformance.md) hold, for the flat-files and raw/processed examples, a directory listing and the [entity records](../reference/entity-record.md) a reader is expected to produce.
