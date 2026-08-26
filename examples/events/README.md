# Multi-call sequence examples

Files in this directory illustrate a *sequence* of operation calls and the resulting event envelopes over time — useful for understanding stateful behavior (identity transitions, duplicate-event suppression) that a single payload can't show on its own.

For a single, standalone example payload per canonical event, see `examples/payloads/` instead.

- `identity-lifecycle.json` — an anonymous session that signs up, is later reset (logout), and a second user logs in on the same device, per `specification/identity.md`.
- `screen-tracking-sequence.json` — a screen navigation sequence illustrating the duplicate `screen_viewed` suppression rule from `specification/screen-tracking.md`.

These are illustrative only. They do not imply that any specific production app or user described here actually exists.
