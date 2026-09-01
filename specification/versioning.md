# Versioning and Compatibility Rules

This contract evolves over time. This document defines how it evolves without breaking implementations or data that already depend on it.

## Three levels of versioning

| Level | Tracked in | What it covers |
|---|---|---|
| **Contract version** | `CHANGELOG.md`, using [Semantic Versioning](https://semver.org/) | The overall specification — every document in `specification/`, `events/`, `metrics/`, and `schema/` |
| **Schema version** | `schema_version` on each event definition (`events/*.yaml`) or metric definition (`metrics/*.yaml`) | The shape of one specific event or one specific metric |
| **SDK version** | `sdk_version` in the event envelope or metric envelope | A given platform adapter's own release — tracks which contract version it implements, but is defined and released by the adapter's own repository, not by this one |

The contract is currently at **1.2.0**.

## Compatible vs. breaking changes

| Change | Classification |
|---|---|
| Adding a new optional property to an event | Compatible |
| Adding a new event | Compatible |
| Adding a new allowed value to an existing `enum` property | Compatible |
| Widening a description or clarifying ambiguous wording without changing behavior | Compatible |
| Changing the meaning of an existing property | Breaking |
| Changing a property's `type` | Breaking |
| Changing a property from optional to required | Breaking |
| Removing a property | Breaking |
| Renaming a property | Breaking |
| Renaming an event | Breaking — migration required |
| Removing an event | Breaking |
| Changing a required envelope field | Breaking |
| Adding a new optional dimension to a metric | Compatible |
| Adding a new metric | Compatible |
| Adding a new allowed value to an existing `enum` dimension | Compatible |
| Changing a metric's `unit` | Breaking |
| Changing a dimension's meaning or `type` | Breaking |
| Changing a dimension from optional to required | Breaking |
| Removing a dimension | Breaking |
| Renaming a dimension | Breaking |
| Renaming a metric | Breaking — migration required |
| Removing a metric | Breaking |

A **compatible** change does not require a `schema_version` bump on the affected event or metric and does not require a contract major version bump — it is documented in `CHANGELOG.md` and, if it changes the contract's minor version, released as such.

A **breaking** change to a specific event or metric requires incrementing that event's or metric's `schema_version` (an integer, starting at `1`) and following the deprecation process below. A breaking change to an envelope itself (event or metric), or to the identity/privacy/error rules that every event and metric depends on, requires a contract major version bump.

## Deprecation

Before an event or property is removed, it must first be marked deprecated:

- an event definition may include `deprecated: true` and `deprecated_since` (the contract version in which it was deprecated)
- a deprecated event or property must continue to be documented and must continue to function as previously specified for at least one full contract major version cycle before removal
- `CHANGELOG.md` must record both the deprecation and, later, the removal

## Renaming

Renaming an event or a required property is always breaking. It is modeled as: introduce the new name as a new, compatible addition; mark the old name deprecated; remove the old name only after the deprecation window above. There is no automated migration tooling in this repository — migration is a documented, manual process for implementers.

## Schema version vs. contract version

An individual event's `schema_version` only changes when that specific event's shape changes in a breaking way. It is entirely possible — and expected — for the contract's overall version to advance (new events added, new optional properties added elsewhere) while a given event's `schema_version` stays at `1` indefinitely, because that event itself never had a breaking change.

## App-specific event schema_version

App-specific events (specification/events.md) are not defined by this contract, so this contract cannot assign, review, or track their `schema_version` the way it does for a canonical event. This section defines the rule every platform implementation follows so that `schema_version` still means the same thing for an app-specific event as it does for a canonical one: a version marker for one specific event's shape, changed only when that shape changes in a breaking way (per the compatible/breaking table above).

1. **What it means.** The same thing as for a canonical event: a version identifier for one specific event name's shape — scoped to whichever application defines that event, since this contract has no definition of its own for it to describe.
2. **Who assigns it.** The application that defines the app-specific event — never this contract, and never a platform adapter acting on its own judgment. An adapter's role is to correctly place whatever version the application has told it into the envelope's `schema_version` field; the adapter does not decide when that number changes.
3. **Initial version.** `1` — the same starting point as a canonical event (specification/versioning.md's `schema_version` starts at `1` throughout this contract). An app-specific event the application has never explicitly versioned is implicitly at version `1`.
4. **When it increments.** Only when the application makes a breaking change (below) to that specific app-specific event's own shape. A compatible change does not require incrementing it.
5. **Breaking change.** The same classification used for a canonical event, applied to the application's own prior shape for that event name: changing a property's meaning, changing a property's type, changing a property from optional to required, removing a property, or renaming the event.
6. **Compatible change.** Also the same classification: adding a new optional property, adding a new allowed value to an existing enum-shaped property, or clarifying documentation without changing behavior.
7. **Independence across applications.** Yes. An app-specific event already carries no cross-app compatibility guarantee (specification/events.md); its `schema_version` carries none either. Two different applications may use the same event name with entirely different shapes and independently-numbered versions — this contract requires no coordination between them and provides none.
8. **Envelope vs. definition.** `schema_version` is always an envelope field (schema/event-envelope.yaml) for every event, canonical or app-specific alike — there is no separate "app-specific event definition" in this contract for it to belong to instead. For a canonical event, the value placed in the envelope comes from this contract's own event definition (events/*.yaml). For an app-specific event, no such central definition exists; the application is responsible for keeping its own record of that event's current version — in whatever form is convenient to it — and supplying it to its platform adapter, which places it in the envelope unchanged.

## Metric schema_version

A metric's `schema_version` (`schema/metric-envelope.yaml`) follows exactly the same rule as an event's: an integer, starting at `1`, that identifies the shape of one specific metric name, and that changes only when that metric's own shape changes in a breaking way (per the compatible/breaking table above). It is entirely possible for the contract's overall version to advance while a given canonical metric's `schema_version` stays at `1` indefinitely, for the same reason a canonical event's can — nothing about that specific metric's shape has had a breaking change.

Every metric defined in this phase (`revenue`, `ad_impression`, `ad_revenue`, `session_duration`, `app_launch_duration`, `screen_load_duration`, `operation_duration`, `handled_error`) is introduced at `schema_version: 1`.

## App-specific metric schema_version

This contract allows app-specific metrics — a `metric_name` an application defines for itself, not among the canonical metrics in `metrics/*.yaml` — on the same basis it already allows app-specific events (`specification/events.md`): the metric envelope (`schema/metric-envelope.yaml`) places no restriction on `metric_name` beyond the identifier shape every name must follow, so an application may record a measurement this contract does not yet name, provided it otherwise follows the full metric envelope (`specification/metric-envelope.md`) — a fixed `unit`, correctly-typed `dimensions`, and every required envelope field.

App-specific metrics are not defined by this contract, so this contract cannot assign, review, or track their `schema_version` the way it does for a canonical metric. This section defines the rule every platform implementation follows, mirroring the app-specific event rule above exactly, so that `schema_version` still means the same thing for an app-specific metric as it does for a canonical one:

1. **What it means.** The same thing as for a canonical metric: a version identifier for one specific metric name's shape (its `unit` and its dimensions) — scoped to whichever application defines that metric, since this contract has no definition of its own for it to describe.
2. **Who assigns it.** The application that defines the app-specific metric — never this contract, and never a platform adapter acting on its own judgment. An adapter's role is to correctly place whatever version the application has told it into the envelope's `schema_version` field; the adapter does not decide when that number changes.
3. **Initial version.** `1` — the same starting point as a canonical metric. An app-specific metric the application has never explicitly versioned is implicitly at version `1`.
4. **When it increments.** Only when the application makes a breaking change (above) to that specific app-specific metric's own shape. A compatible change does not require incrementing it.
5. **Breaking change.** The same classification used for a canonical metric, applied to the application's own prior shape for that metric name: changing its `unit`, changing a dimension's meaning or type, changing a dimension from optional to required, removing a dimension, or renaming the metric.
6. **Compatible change.** Also the same classification: adding a new optional dimension, adding a new allowed value to an existing enum-shaped dimension, or clarifying documentation without changing behavior.
7. **Independence across applications.** Yes. An app-specific metric carries no cross-app compatibility guarantee, exactly like an app-specific event; its `schema_version` carries none either. Two different applications may use the same metric name with entirely different shapes and independently-numbered versions — this contract requires no coordination between them and provides none.
8. **Envelope vs. definition.** `schema_version` is always an envelope field (`schema/metric-envelope.yaml`) for every metric, canonical or app-specific alike — there is no separate "app-specific metric definition" in this contract for it to belong to instead. For a canonical metric, the value placed in the envelope comes from this contract's own metric definition (`metrics/*.yaml`). For an app-specific metric, no such central definition exists; the application is responsible for keeping its own record of that metric's current version — in whatever form is convenient to it — and supplying it to its platform adapter, which places it in the envelope unchanged.

## What implementers must preserve

A conforming implementation must:

- emit the `schema_version` that matches the event or metric definition it is implementing
- never silently reinterpret a property's or dimension's meaning while keeping its name and `schema_version` unchanged
- report its own `sdk_version` accurately, so that downstream consumers can reason about which contract version, and which event or metric shapes, produced a given payload
