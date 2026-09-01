# Platform Implementation Guide

This document is for teams building a platform adapter (SDK) that implements the InfinityForge Tracking Contract for a specific app template — React Native today, Swift and Kotlin already or soon, and whatever comes after that.

It does not contain implementation code. It explains what an adapter is responsible for, and how to know whether it conforms.

## Where an adapter sits

```
Tracking Contract
        |
        +--> React Native implementation
        |
        +--> Swift implementation
        |
        +--> Kotlin implementation
        |
        +--> Future implementations
```

This repository defines the contract once. Each box above is a separate implementation, living in its own app template or a future dedicated SDK repository — never in this repository. Every box must independently satisfy the same contract.

## What every implementation must do

Regardless of language or platform, a conforming adapter must:

- **Expose the same conceptual API.** All six core operations from `specification/api.md` (`initialize`, `track`, `identify`, `setUserProperties`, `screen`, `reset`), under whatever calling convention is idiomatic for the platform. The names, argument order, and calling style are the adapter's own choice — the behavior is not.
- **Produce compatible event schemas.** Every event emitted matches `schema/event-envelope.yaml`, and every canonical event it emits matches its definition in `events/*.yaml` — same field names, same required/optional status, same types, same `snake_case` casing (`specification/conventions.md`), regardless of what casing convention is idiomatic inside the adapter's own language.
- **Follow the same identity rules.** `specification/identity.md`, without exception — including generating a new `anonymous_id` on `reset`, not reusing the old one.
- **Follow the same privacy rules.** `specification/privacy.md`. An adapter must not make it easier for application code to accidentally violate these rules than to follow them — for example, it should not expose a convenience method that encourages passing arbitrary free-form objects as event properties without any review.
- **Follow the same error semantics.** `specification/errors.md` — no operation may crash the host app or block a user-facing action, regardless of what the platform's native error-handling idioms look like.
- **Preserve schema versions.** Emit the `schema_version` that matches the event definition being implemented, and report its own `sdk_version` (and, ideally, `sdk_name` — see `specification/metadata.md`) accurately.

## What is intentionally left to each implementation

- The literal method/function names and calling convention
- Internal architecture, threading model, and persistence mechanism
- Which analytics provider(s), if any, ultimately receive the data, and how they are configured
- Batching, retry, and network transport behavior
- Additional convenience APIs, as long as they don't violate the rules above

Two adapters do not need to look alike. They need to produce data that means the same thing.

## Conformance checklist

Before considering a platform adapter complete, verify:

- [ ] All six operations from `specification/api.md` are implemented and behave as specified
- [ ] Emitted events validate against `schema/event-envelope.yaml`
- [ ] Every canonical event emitted matches its `events/*.yaml` definition (required properties present, types correct, `schema_version` correct)
- [ ] Identity behavior matches `specification/identity.md`, including the anonymous → authenticated transition and `reset` issuing a new `anonymous_id`
- [ ] Screen tracking behavior matches `specification/screen-tracking.md`, including duplicate suppression
- [ ] No prohibited data category from `specification/privacy.md` can reach an event through the adapter's normal usage
- [ ] No operation can throw an uncaught exception or block a user-facing action, per `specification/errors.md`
- [ ] The adapter's own version is reported accurately as `sdk_version`

If the adapter also supports the optional Metrics capability, additionally verify:

- [ ] `recordMetric` is implemented and behaves as specified in `specification/api.md`
- [ ] Emitted metrics validate against `schema/metric-envelope.yaml`
- [ ] Every canonical metric emitted matches its `metrics/*.yaml` definition (fixed `unit`, required dimensions present, types correct, `schema_version` correct)
- [ ] No prohibited data category from `specification/privacy.md`, including its metrics-specific subsection, can reach a dimension through the adapter's normal usage
- [ ] `recordMetric` cannot throw an uncaught exception or block a user-facing action, per `specification/errors.md`'s metrics subsection

## Provider independence and future providers

This contract is deliberately independent of any specific analytics vendor. An adapter may send events to one provider, several, or none yet — that choice, and any provider-specific integration code, belongs entirely inside the adapter, never in this repository.

Providers an implementation might eventually integrate with include (without this repository selecting or endorsing any of them):

- Firebase Analytics
- Amplitude
- a custom InfinityForge backend
- other analytics systems, present or future

If InfinityForge changes which provider(s) an app template sends data to, that is a change to the adapter, not to this contract. The contract remains valid, and existing event data remains meaningful, regardless of which provider is receiving it at any given time.

## Implementing the Metrics capability

`specification/metrics.md`, `specification/metric-envelope.md`, and `metrics/*.yaml` define an optional, additive capability layer on top of the base six-operation contract (`specification/contract.md`'s "Metric conformance" section). An adapter is not required to implement it; if it does, `recordMetric` must be implemented completely, not partially.

- **Mapping a provider's own concepts onto the normalized shape.** A billing/subscription provider's transaction callback maps onto `revenue` (`metrics/monetization.yaml`); an advertising mediation SDK's impression- and revenue-level callbacks map onto `ad_impression`/`ad_revenue` (`metrics/advertising.yaml`). Whatever native shape a provider reports in — a delegate callback, a promise, a provider-specific object — the adapter is responsible for translating it into the normalized envelope and dimensions this contract defines; no provider-specific field name or structure should leak into the emitted `dimensions` or `source` value.
- **Providers an implementation might eventually integrate with for metrics** include, without this repository selecting or endorsing any of them: a billing/subscription provider, an advertising mediation SDK, a custom InfinityForge backend, or other measurement systems, present or future. As with events, this repository names no specific vendor as required or assumed.
- **`typical_source` is guidance, not enforcement.** Each canonical metric definition documents a `typical_source` (`specification/metric-envelope.md`), but an adapter may legitimately use a different `source` category when its actual measurement genuinely comes from a different kind of system — the schema does not hard-lock `source` per metric name.
- **Do not invent a derived metric.** An adapter must never calculate and emit a derived business/analytics number (DAU, LTV, MRR, conversion rate, or similar — `specification/derived-metrics.md`) as if it were a raw metric. If a provider SDK exposes such a calculated value directly, the adapter should not forward it through `recordMetric` at all — that calculation belongs downstream, not on-device.

## Adding a new platform template

A new platform template (Flutter, web, Unity, or anything else) implements this contract exactly the same way an existing one does: by building an adapter that satisfies the conformance checklist above. This repository should not need to change merely because a new platform is added — if it does need to change, that's a signal the contract had an unjustified platform-specific assumption baked into it, which should be raised via `CONTRIBUTING.md`.
