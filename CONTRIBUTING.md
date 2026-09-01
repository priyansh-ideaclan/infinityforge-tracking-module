# Contributing to the InfinityForge Tracking Module

This repository is the source of truth for the InfinityForge Tracking Contract. Because every platform template depends on it, changes here are reviewed more carefully than changes to a single application.

## Before you propose a change

Read:

1. [`specification/overview.md`](specification/overview.md) — the design principles this contract is built on
2. [`specification/versioning.md`](specification/versioning.md) — how to classify your change as compatible or breaking
3. [`specification/privacy.md`](specification/privacy.md) — if your change adds a new property or event, it must not collect prohibited data

## What kinds of changes are welcome

- New optional properties on an existing event (compatible change)
- New events that fit an existing category, or a clearly justified new category
- New optional dimensions on an existing metric (compatible change)
- New metrics that fit an existing category, or a clearly justified new category — only when the underlying measurement has no reasonable home as an existing event or as a dimension on an existing metric (`specification/metric-taxonomy.md`'s "Adding a new metric")
- Clarifications to specification documents that resolve ambiguity without changing behavior
- New illustrative examples
- Improvements to the validation tooling

## What requires extra scrutiny

- Anything that changes the *meaning* of an existing field, event, or metric (breaking change — see `specification/versioning.md`)
- Anything that removes or renames an event, a metric, or a required property/dimension (breaking change)
- Any new property, event, metric, or dimension intended to capture data that could be sensitive personal information — this requires explicit privacy review per `specification/privacy.md` before it is added, not after
- Any change to the identity model (`specification/identity.md`)
- Any change to the event envelope (`schema/event-envelope.yaml`) or the metric envelope (`schema/metric-envelope.yaml`)
- Any proposal for a metric whose value is a *derived* business/analytics number (DAU, LTV, MRR, conversion rate, or similar) rather than a raw measurement — see `specification/derived-metrics.md`; these are out of scope for this contract by design, not merely unreviewed

## Checklist for adding a new event

1. Confirm the event doesn't already exist under a different name — check `events/*.yaml`.
2. Choose a category (`application`, `authentication`, `onboarding`, `product`, `monetization`, or propose a new one if none fit).
3. Name it in `snake_case` following [`specification/conventions.md`](specification/conventions.md).
4. Write `description`, `trigger`, and `purpose` in plain, implementation-neutral language — no mention of any specific framework, navigation library, or analytics vendor.
5. Define its properties: for each, a `name`, `type`, whether it is `required`, and a `description`. Only mark a property `required` if its semantics are unambiguous — see [`specification/events.md`](specification/events.md) for guidance on common vs. app-specific properties.
6. Set `schema_version: 1` for a brand-new event.
7. Add a corresponding example payload under `examples/payloads/`.
8. Run the validation script (`validation/validate.py`) before opening a pull request.

## Checklist for changing an existing event or the envelope

1. Classify the change using the compatibility table in `specification/versioning.md`.
2. If it is breaking, follow the deprecation process described there rather than editing the field in place.
3. Update the affected event's `schema_version` if, and only if, the change is a breaking change to that event's shape.
4. Update `CHANGELOG.md`.
5. Update any affected examples.

## Checklist for adding a new metric

1. Confirm the measurement doesn't already exist under a different name, and doesn't already have a reasonable home as an existing event or as a dimension on an existing metric — check `metrics/*.yaml` and `events/*.yaml`, and see `specification/metric-taxonomy.md`'s "Adding a new metric" and "Category boundaries."
2. Confirm it is a raw fact, not a derived/aggregated business metric — see `specification/derived-metrics.md`. If it is derived, it does not belong here as a metric at all.
3. Choose a category (`monetization`, `advertising`, `engagement`, `performance`, `reliability`, or propose a new one if none fit).
4. Name it in `snake_case` following [`specification/conventions.md`](specification/conventions.md).
5. Write `description`, `trigger`, and `purpose` in plain, implementation-neutral language — no mention of any specific framework, navigation library, or analytics/ad/billing vendor.
6. Fix its `unit` (`currency`, `count`, `impression`, `millisecond`, `second`, or `other`) — a metric's unit is not chosen per-call — and its `typical_source`, per `specification/metric-envelope.md`.
7. Define its dimensions: for each, a `name`, `type` (`string`, `integer`, `boolean`, or `enum` only), whether it is `required`, and a `description` — `allowed_values` when `type: enum`. Only mark a dimension `required` if a measurement is not meaningfully interpretable without it (as `revenue`'s `transaction_type` is).
8. Set `schema_version: 1` for a brand-new metric.
9. Add a corresponding example payload under `examples/metrics/`.
10. Add the new metric to `specification/metric-taxonomy.md`'s summary table.
11. Run the validation script (`validation/validate.py`) before opening a pull request.

## Checklist for changing an existing metric or the metric envelope

1. Classify the change using the compatibility table in `specification/versioning.md`.
2. If it is breaking, follow the deprecation process described there rather than editing the field in place.
3. Update the affected metric's `schema_version` if, and only if, the change is a breaking change to that metric's shape.
4. Update `CHANGELOG.md`.
5. Update any affected examples and `specification/metric-taxonomy.md`.

## Where things belong

| Content | Location |
|---|---|
| Normative rules and semantics | `specification/` |
| Canonical event definitions | `events/` |
| Canonical metric definitions | `metrics/` |
| Machine-readable envelope/property/dimension schema | `schema/` |
| Illustrative payloads | `examples/` |
| Guidance for platform implementers | `docs/` |

Platform-specific implementation code never belongs in this repository, regardless of how small. It belongs in the relevant app template or a future dedicated SDK repository.

## Review

Pull requests are reviewed for:

- language-independence (no vendor or framework references leaking into `specification/`, `events/`, `metrics/`, or `schema/`)
- consistency with existing terminology (see `specification/conventions.md`)
- correct compatible/breaking classification
- privacy compliance for any new data collection
- for a new metric: that it is a raw fact, not a derived business/analytics number (`specification/derived-metrics.md`), and that it isn't a duplicate of an existing event or dimension

Use `validation/validate.py` to catch structural and terminology issues before requesting review.
