# preferences

`preferences` is an optional top-level object holding runtime context: which computing environment is active and which data location to use when none is specified.

`additionalProperties` is `false`.

## Fields

### `environmentIdentifier`

| | |
|--|--|
| Type | `string` |
| Example | `"windows-lab"`, `"mac-analysis"`, `"hpc-cluster"` |

Selects, in every data location, the `rootStoragePath` whose `environment` matches. Not needed when the config is used on one environment and its root paths carry no `environment`.

### `defaultDataLocationIdentifier`

| | |
|--|--|
| Type | `string` |

The location a tool operates on when not told otherwise. Must be a `dataLocations` identifier.

## The local overlay

These values describe a machine or a user session, not the dataset, and they change from checkout to checkout. Keeping them only in a shared, version-controlled config makes every machine fight over the same line. So:

- `preferences` may be omitted from the shared config, and so may `path` on a `rootStoragePath`: a config shipped with a published dataset has no path that holds for every user.
- A reader that finds a file named **`<config basename>.local.json`** next to the config applies it: its `preferences` replace the shared ones, and each `rootStoragePaths` entry sets the `path` of the root it names, keyed by data location and root identifier. The overlay holds these two keys and nothing else, and it is meant to be git-ignored.

```json
{
  "preferences": {
    "defaultDataLocationIdentifier": "processed",
    "environmentIdentifier": "mac-analysis"
  },
  "rootStoragePaths": [
    { "dataLocationIdentifier": "raw", "rootStoragePathIdentifier": "analysis-mac", "path": "/Volumes/DATA/TwoPhoton" }
  ]
}
```

The overlay composes with `environment` on the root paths: `environment` says which of the roots a lab knows is the active one on this machine, the overlay says where that root is on this checkout. An entry that names no root of the config is refused as `reference-integrity`, a malformed overlay as `schema-validation`, and the merged config is validated again. Walking a listing needs no path at all; a reader that has to open files (a `function` extractor) under a root without one reports it in the walk's warnings and passes paths relative to the root.

Whether a root path is currently reachable is runtime state as well; readers report it, the config does not store it.
