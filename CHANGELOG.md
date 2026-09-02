# Changelog

All notable changes to the InfinityForge Tracking Contract are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [`specification/versioning.md`](specification/versioning.md).

## [Unreleased]

### Fixed

- Encoded `handled_error`'s existing `value == 1` rule as `fixed_value: 1`, so machine-readable contract consumers and validation enforce the same semantics already required by the normative prose.

## [1.2.0] - 2026-09-01

### Added

- **Metrics / Telemetry model** — a second conceptual primitive, the **Metric** (a raw, measured value + unit, distinct from an Event's named-occurrence shape), alongside a new optional `recordMetric` operation (`specification/api.md`) and an optional, additive "Metric conformance" capability layer (`specification/contract.md`) that does not change base six-operation conformance.
- `specification/metrics.md`: the primary normative document — the Event/Raw Measurement/Derived Metric distinction, the full semantic model for eight canonical metrics (revenue, ad impressions, ad revenue, purchases, subscriptions, engagement, performance, reliability), and documented, reasoned exclusions for notification, attribution/acquisition, and conversion metrics.
- `specification/metric-envelope.md`: the metric envelope field-by-field specification — value/unit/currency semantics (including how direction, e.g. a refund, is represented without a signed value), source semantics, and dimension governance.
- `specification/metric-taxonomy.md`: the canonical metric list, organized by category (monetization, advertising, engagement, performance, reliability).
- `specification/derived-metrics.md`: the dedicated rule that a derived business/analytics metric (DAU, WAU, MAU, retention, MRR, ARR, churn, LTV, ARPU, ARPPU, eCPM, ROAS, conversion rate) is a downstream calculation and must never be emitted as a client tracking fact, plus the underlying-facts mapping for each.
- `schema/metric-envelope.yaml`: the machine-readable metric envelope, reusing (never redefining) the identity/metadata fields already defined for the event envelope.
- `schema/metric-dimensions.yaml`: the machine-readable metric dimension shape (deliberately narrower type set than event properties: `string`/`integer`/`boolean`/`enum` only).
- `schema/common-types.yaml`: three new shared `$defs` — `metric_value`, `metric_unit`, `metric_source`.
- `metrics/monetization.yaml`, `metrics/advertising.yaml`, `metrics/engagement.yaml`, `metrics/performance.yaml`, `metrics/reliability.yaml`: eight new canonical metrics — `revenue`, `ad_impression`, `ad_revenue`, `session_duration`, `app_launch_duration`, `screen_load_duration`, `operation_duration`, `handled_error` — each at `schema_version: 1`.
- `examples/metrics/`: one full example payload per canonical metric (eight files).
- `specification/versioning.md`: "Metric schema_version" and "App-specific metric schema_version" sections, mirroring the existing event `schema_version` rules exactly, plus metric-specific rows in the compatible/breaking change table.
- `specification/privacy.md`: a "Metrics and dimensions" subsection extending the existing prohibited-data-category and low-cardinality rules to `dimensions`, `reference_id`, and `error_code`.
- `specification/errors.md`: a "Metrics" subsection extending the non-negotiable error-handling rules and the "what counts as malformed" definition to `recordMetric` and the metric envelope.
- `specification/api.md`: the `recordMetric` operation, documented in full (purpose, inputs, required/optional fields, expected behavior, identity implications, failure behavior, privacy considerations), explicitly marked as optional/capability-gated rather than part of base conformance.
- `specification/contract.md`: a "Metric conformance (optional capability)" section defining the all-or-nothing conformance rule for the Metrics capability.
- `specification/overview.md`, `README.md`, `CONTRIBUTING.md`, `docs/implementation-guide.md`: updated to reference the new specification documents, repository structure, and metric-specific contribution/conformance checklists.
- `validation/validate.py`: metric definition validation, metric example validation, `admob`/`revenuecat`/`google analytics` added to the forbidden-vendor-term list, and `metrics`/`examples` added to the directories scanned for forbidden terms.

### Changed (compatible)

- `events/monetization.yaml`: added an optional `transaction_id` property to `purchase_completed`, `subscription_started`, and `subscription_cancelled` — the standard linkage point to an accompanying `revenue` metric measurement (via `reference_id`). No `schema_version` bump on any of the three events, per the compatible-change rule in `specification/versioning.md`.
- `examples/payloads/purchase_completed.json`, `examples/payloads/subscription_started.json`, `examples/payloads/subscription_cancelled.json`: updated to include an example `transaction_id`.

### Notes

- This release is specification-only. No platform implementation (React Native, Swift, Kotlin) was added, changed, or generated as part of this release — see the phase's own final report for explicit confirmation.
- The contract's overall minor version advances (1.1.0 → 1.2.0) because this release is purely additive: new optional fields on existing events, new canonical metrics, and an entirely new but optional capability layer. Nothing existing changes meaning, type, or required/optional status.

## [1.1.0] - 2026-08-26

### Added

- `specification/versioning.md`: an explicit "App-specific event schema_version" rule — what it means, who assigns it (the application, never this contract or a platform adapter), that it starts at `1`, when it increments, what counts as a breaking vs. compatible change to it, that different applications version their own app-specific events independently, and that it is always an envelope field, never a separate central definition. Closes a gap platform implementers had previously been left to assume on their own.
- `specification/metadata.md`: an "Environment fallback" subsection documenting the narrow, accepted exception under which an implementation may resolve `environment` from a build-time development/not-development signal instead of an explicit configured value, without violating the "never silently default to production when unknown" rule — conditioned on the signal only ever distinguishing `development` from *not* `development`, defaulting to `production` (not `preview`) in the fallback case, and surfacing a diagnostic when it fires.
- `specification/events.md`: cross-reference to the new app-specific `schema_version` rule.

## [1.0.0] - 2026-08-26

### Added

- Initial publication of the InfinityForge Tracking Contract.
- Core tracking operations: `initialize`, `track`, `identify`, `setUserProperties`, `screen`, `reset` (`specification/api.md`).
- Canonical event envelope and metadata ownership model (`schema/event-envelope.yaml`, `specification/metadata.md`).
- Identity model covering anonymous/authenticated state, login, logout, and account switching (`specification/identity.md`).
- Screen tracking semantics (`specification/screen-tracking.md`).
- Privacy rules and prohibited data categories (`specification/privacy.md`).
- Error-handling rules (`specification/errors.md`).
- Versioning and compatibility rules (`specification/versioning.md`).
- Property and naming conventions (`specification/conventions.md`).
- Initial event taxonomy across five categories — application, authentication, onboarding, product, monetization — totaling 14 canonical events (`events/`).
- Machine-readable schema for the envelope and event property definitions (`schema/`).
- Illustrative example payloads for every canonical event (`examples/`).
- Platform implementation guidance (`docs/implementation-guide.md`).
- Lightweight, dependency-light validation tooling (`validation/`).
