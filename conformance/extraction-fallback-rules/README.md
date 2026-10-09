# extraction-fallback-rules

Several `metadataMapping` rules for one field in one location are an ordered fallback: the first rule in config order that yields a value wins, and a later rule neither overwrites that value nor removes it when it yields nothing.

What it checks:

- `session_id` has two `regex` rules for two naming forms, `<date>_<name>` and `<name>_<date>`. Each session folder matches exactly one of them, and the identity comes from whichever rule yields.
- `source` has two `fixed` rules; the record carries `first`.
- `tag` has a `regex` that matches nothing and then a `fixed` value; the record carries `untagged` and no `extraction-failed`.
- `session_label` is a `template` over `session_id`. It is evaluated after both `session_id` rules have run, so it composes with the value the fallback produced.
