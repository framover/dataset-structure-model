# extraction-fallback-rules

Several `metadataMapping` rules for one field in one location are an ordered fallback: a rule is evaluated only when it is the first remaining rule for its field and, for a template, no other field it references still has a remaining rule. The first rule that yields a value wins and the field's later rules are not evaluated; a later rule neither overwrites that value nor removes it.

What it checks:

- `session_id` has two `regex` rules for two naming forms, `<date>_<name>` and `<name>_<date>`. Each session folder matches exactly one of them, and the identity comes from whichever rule yields.
- `source` has two `fixed` rules; the record carries `first`.
- `tag` has a `regex` that matches nothing and then a `fixed` value; the record carries `untagged` and no `extraction-failed`.
- `session_label` is a `template` over `session_id`. It is evaluated after both `session_id` rules have run, so it composes with the value the fallback produced.
- `day_label` is a `template` over `day` placed before a `fixed` fallback, and both `day` rules come after it in the config. The template is deferred until `day` has run and holds back the fallback meanwhile, so the record carries `<day>-label`, not `no-day`.
