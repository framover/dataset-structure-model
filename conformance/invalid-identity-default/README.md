# invalid-identity-default

A config that passes JSON Schema validation but puts a `defaultValue` on `session_id`, the single identity field of `session`. A reader must refuse it with error code `reference-integrity`: with such a default, every folder that matched the level but yielded no id would collapse into one entity and nothing would be reported `no-match`. A default is allowed only on a part of a composite identity (`identifierRefs` with more than one field); see `composite-identity-default`.
