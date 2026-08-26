# The Tracking Contract

This document defines what it means for a platform implementation to **conform** to InfinityForge tracking. The detailed, field-by-field specification of each operation lives in `specification/api.md`; this document defines the guarantees that hold across all of them.

## The six operations

Every conforming implementation exposes exactly six conceptual operations:

| Operation | Purpose |
|---|---|
| `initialize` | Prepare the tracking system and establish an identity before any events are recorded |
| `track` | Record that a named event occurred |
| `identify` | Bind the current session to a known `user_id` |
| `setUserProperties` | Attach or update persistent, user-level attributes |
| `screen` | Record that the user is now viewing a given screen |
| `reset` | Clear identity and user-level state, returning to a fresh anonymous identity |

These are conceptual operations, not method signatures. A conforming adapter may name, group, or expose them however is idiomatic for its language — what must be preserved is the behavior described in `specification/api.md`, not any particular calling convention.

## Conformance requirements

A platform implementation conforms to this contract if all of the following hold:

1. **Operation coverage.** All six operations are exposed in some form, and each behaves according to `specification/api.md`.
2. **Envelope compatibility.** Every event emitted matches the structure defined in `schema/event-envelope.yaml` — the same fields, the same required/optional status, the same types.
3. **Event compatibility.** Every canonical event (`events/*.yaml`) that the implementation emits uses the documented name, and its documented properties use the documented types and required/optional status. An implementation is not required to emit every canonical event, but any canonical event it does emit must match its definition.
4. **Identity compliance.** The implementation follows the anonymous/authenticated identity model in `specification/identity.md`, including `reset` behavior.
5. **Screen semantics.** Any `screen` calls follow `specification/screen-tracking.md`.
6. **Privacy compliance.** The implementation does not emit any of the prohibited data categories in `specification/privacy.md`, and provides no easier path for application code to do so than following this contract correctly.
7. **Error isolation.** The implementation follows `specification/errors.md` — tracking failures are contained and never surface as application crashes or blocked user flows.
8. **Version discipline.** The implementation preserves `schema_version` per event and correctly reports its own `sdk_version`, per `specification/versioning.md`.

An implementation may add app-specific events and app-specific properties beyond this contract (see `specification/events.md` for the common-vs-app-specific distinction). Doing so does not break conformance, as long as the app-specific additions themselves follow `specification/conventions.md` and `specification/privacy.md`.

## Cross-platform guarantees

Because every conforming implementation follows the same envelope, the same identity model, and the same canonical event definitions, data collected from different app templates can be:

- **joined** on `user_id` / `anonymous_id` across platforms
- **compared** for the same canonical event across platforms, because required fields and types are guaranteed identical
- **evolved** without breaking existing consumers, because compatible vs. breaking changes are classified consistently (`specification/versioning.md`)

## What this contract intentionally leaves open

- **Transport.** How events physically leave the device (batching, retry, network protocol) is not specified. This contract describes what an event *is*, not how it travels.
- **Storage.** Where or how an implementation persists `anonymous_id`, `user_id`, or user properties on-device is not specified, beyond the durability implied by `specification/identity.md` (e.g., identity should survive an app restart).
- **Provider selection.** Which analytics vendor(s), if any, ultimately receive this data is not specified here — see `specification/versioning.md` and `docs/implementation-guide.md` for how provider-independence is preserved.
- **Configuration surface.** `initialize` inputs beyond `app_id` and `environment` are implementation-defined.

## Non-goals

This contract does not attempt to guarantee delivery, ordering across a network boundary, deduplication at an ingestion backend, or compliance with any specific privacy regulation. Those are properties of the systems built on top of this contract, not of the contract itself.
