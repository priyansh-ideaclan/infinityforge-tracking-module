# Error-Handling Rules

Tracking is not core application functionality. These rules exist so that no InfinityForge app template ever ships a bug or an outage caused by its analytics layer.

## Non-negotiable rules

1. **Analytics failure must never crash the app.** No uncaught exception, no unhandled promise rejection, no fatal error may originate from any of the six operations, under any input.
2. **Analytics must never block critical application behavior.** None of the six operations may synchronously block a user-facing action — navigation, input, or rendering must never wait on tracking to complete.
3. **Malformed events must be rejected or safely handled, never propagated as a crash.** A malformed event (see below) must be either corrected, dropped, or queued for later handling — but never allowed to raise an error the calling application must catch.
4. **Provider failures must be isolated.** If an implementation forwards events to one or more downstream analytics providers, a failure in one provider (network error, rejection, timeout) must not affect delivery to any other provider, and must not affect the application at all.
5. **Implementations should expose useful diagnostics during development.** In `development` (see `metadata.md`), a conforming implementation should make tracking problems visible — for example, logging when an event is malformed, when a required field is missing, or when an unrecognized event name is used — so issues are caught before release.
6. **Production diagnostics must not leak sensitive information.** Whatever diagnostic surface exists in `production` (if any) must not include raw property values, user identifiers beyond what's already in the event, or any of the categories prohibited in `privacy.md`.

This contract does not prescribe a specific logging vendor, log format, or diagnostic tool — only the behavior above.

## What counts as malformed

An event is malformed if any of the following hold:

- a required envelope field is missing, empty, or the wrong type (`schema/event-envelope.yaml`)
- a property marked `required` on a canonical event definition is missing
- a property's value does not match its documented `type`
- an `enum` property's value is not among its allowed values (see `conventions.md` for how unknown enum values should be handled when *receiving*, as opposed to *emitting*, data — this rule is about what an implementation emits)
- `event` or a property key is not `snake_case` per `conventions.md`

## Unknown or custom event names

This contract does not forbid an application from tracking an event name outside the canonical taxonomy (`events/*.yaml`). App-specific events are permitted, provided they follow `conventions.md` and `privacy.md`. Such events carry no cross-app compatibility guarantee — they are not defined by this contract, so no other InfinityForge app or platform team is obligated to interpret them the same way. Implementations should log a development diagnostic when an app-specific (non-canonical) event name is used, purely as a visibility aid, not as an error.

## Handling malformed input

When `track`, `screen`, `identify`, or `setUserProperties` receives malformed input, a conforming implementation must, in order of preference:

1. Correct what can be unambiguously corrected (for example, coercing a clearly-typed value), or
2. Drop the offending event/property and continue, or
3. Queue it for later resolution if the implementation supports that

At no point may the calling application observe an exception it must handle, nor may the rest of the event (or subsequent events) be silently corrupted as a result.
