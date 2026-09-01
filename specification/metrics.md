# Metrics / Telemetry Model

This document extends the InfinityForge Tracking Contract with a second conceptual primitive — the **Metric** — alongside the **Event** primitive `contract.md`, `api.md`, and `events.md` already define. It does not redesign anything about Events: the six core operations, the event envelope, the event taxonomy, identity, privacy, error handling, and versioning rules all apply, unchanged, to everything they already governed. This document defines what a Metric is, when to use one instead of (or alongside) an Event, and the full semantic model for the specific measurement categories this phase adds.

Read this document alongside `metric-envelope.md` (the field-by-field envelope spec), `metric-taxonomy.md` (the canonical metric list), and `derived-metrics.md` (the raw-vs-derived rule and per-derived-metric fact list) — together these four documents are the complete Metrics/Telemetry specification.

## 1. Why a second primitive

An **Event** (existing) is a discrete, named business occurrence — its defining characteristic is *what kind of thing happened*, described through arbitrary application-defined properties. A **Metric** (new) is a raw, measured **value** at a point in time — its defining characteristic is *how much, how many, or how long*, expressed as a number with a unit (and, for money, a currency).

Both are facts. Neither is a derived/aggregated business metric (see section 2C and `derived-metrics.md`). The distinction exists because some raw facts genuinely have no meaningful "name and properties" shape — an ad impression's value isn't a property of an event called `ad_impression`, it *is* a count; a latency measurement isn't meaningfully "described," it's measured. Forcing every quantitative observation into the Event shape would mean either inventing a `value` property on arbitrary events (with no consistent unit, currency, or source semantics — exactly the ambiguity `conventions.md` already warns against: "Do not allow ambiguous values such as `value = 100` without defining what 100 represents") or not capturing it at all.

## 2. Events vs. Raw Measurements vs. Derived Metrics

### A. Events

Facts about something that happened, recorded via `track`/`screen` (`api.md`), matching `schema/event-envelope.yaml` and, for canonical events, `events/*.yaml`. Examples already in this contract: `signup_completed`, `feature_used`, `subscription_started`.

**Use an Event when** the fact is best described by a name and a set of descriptive properties, and no single numeric value is the point of the fact — the point is that something specific occurred.

**Do not use an Event when** the fact is fundamentally a quantitative measurement with a unit — use a Metric instead (section 2B), so the value carries unambiguous unit/currency/source semantics rather than being one more untyped property.

### B. Raw Measurements (Metrics)

Numerical or quantitative observations, recorded through `recordMetric` — a new conceptual operation this phase adds to `specification/api.md`, alongside the existing six (see `contract.md`'s "Metric conformance" section for how this operation relates to the base six-operation contract) — matching `schema/metric-envelope.yaml` and, for canonical metrics, `metrics/*.yaml`. Examples this phase adds: `revenue`, `ad_revenue`, `ad_impression`, `latency`/`duration`-shaped measurements, counts.

**Use a Metric when** the fact's defining characteristic is a value + unit (an amount of money, a count, a duration) — see `metric-envelope.md` for the full value/unit/currency model.

**Do not use a Metric when** the fact is a discrete, nameable business occurrence better served by descriptive properties than a single value — that's an Event. A Metric may accompany an Event (see section 3.1's revenue-vs-purchase_completed relationship) but is never a replacement for one, and vice versa.

### C. Derived Metrics

Values calculated from a *collection* of events and/or measurements — DAU, retention, LTV, MRR, ARPU, churn, eCPM, ROAS, conversion rate, and similar. See `derived-metrics.md` for the full, dedicated normative treatment.

**Never emit a derived metric as a client tracking fact.** A conforming implementation must not define an event or a metric whose value is itself one of these calculated numbers. `derived-metrics.md` documents, for each one, which raw facts (events and/or metrics this contract does define) are required to calculate it downstream.

## 3. Metric capabilities

Each subsection below follows the same structure: Definition, Purpose, Required fields, Optional fields, Example, Validation rules, Versioning implications, Privacy considerations, and Provider implementation guidance. "Required/optional fields" lists **metric-specific** requirements only — every metric additionally carries the full envelope defined in `metric-envelope.md` (required: `metric_name`, `schema_version`, `value`, `unit`, `source`, `timestamp`, `app_id`, `environment`, `platform`, `sdk_version`, `app_version`, `anonymous_id`; optional: `sdk_name`, `user_id`, `currency`, `reference_id`, `dimensions`).

### 3.1 Revenue

**Definition.** `revenue` (`metrics/monetization.yaml`) — a monetary value realized from the user, in either direction (a charge, or a refund/adjustment of one).

**Relationship to existing monetization events.** This is the section most likely to be misread as redefining `events/monetization.yaml`, so it is stated plainly: it does not. `paywall_viewed`, `trial_started`, `subscription_started`, `subscription_cancelled`, and `purchase_completed` remain, unchanged, the canonical record that a monetization **business occurrence** happened. `revenue` is the normalized **measurement** of monetary value realized. The two are complementary, not duplicative:

- A `purchase_completed` or `subscription_started` event typically has an accompanying `revenue` measurement, linked by a shared identifier (the event's optional `transaction_id` property, added in this phase as a compatible addition — see `events/monetization.yaml` — matching the metric's `reference_id`).
- Some monetization occurrences that realize revenue have **no corresponding event today** — a subscription renewal charge (there is no `subscription_renewed` event in this contract) or a refund (there is no refund event). For these, `revenue` stands alone.
- `purchase_completed`'s `price`/`currency` properties and `revenue` are not in conflict: the event property describes the purchase as a business occurrence; the metric is the normalized fact a downstream system aggregates across *all* revenue sources — purchases, subscriptions, renewals, and refunds alike — without needing to know which event type, if any, accompanied each one.

**Purpose.** The single normalized monetary fact downstream systems use for MRR, ARR, LTV, ARPU, and ARPPU (`derived-metrics.md`). This contract does **not** define those derived metrics as client facts — see section 2C.

**Required fields.** `dimensions.transaction_type` (`charge` / `refund` / `adjustment` — required because `value` is always a non-negative magnitude; see `metric-envelope.md`'s "Representing direction" rule). `unit` is fixed to `currency`, so `currency` is required.

**Optional fields.** `dimensions.billing_type` (`subscription` / `one_time` / `other`), `dimensions.product_id`, `reference_id` (linking to an accompanying event's `transaction_id`, when one exists).

**Example.** `examples/metrics/revenue.json`.

**Validation rules.** See section 9. Specifically: `currency` present (required for `unit: currency`); `transaction_type` present and one of the allowed values; `value` non-negative.

**Versioning implications.** `revenue`'s own `schema_version` (currently `1`) follows the identical model as an event's — see section 11 / `versioning.md`.

**Privacy considerations.** `product_id`/`plan`-style dimensions must be stable identifiers, never free text (`privacy.md`). `reference_id` must be an opaque transaction identifier, never itself PII (for example, never a payment card's PAN or a customer's raw billing name).

**Provider implementation guidance.** A payment/subscription provider adapter typically has direct access to a confirmed transaction amount and currency; `docs/implementation-guide.md` covers how provider-specific purchase/subscription callbacks map onto this normalized shape.

**Decision log — what this section deliberately does not define.** This contract does not invent gross-vs-net accounting beyond the `value`-is-gross rule in `metric-envelope.md`, and does not model platform fees, taxes, or acquisition-spend-adjusted revenue. Doing so would require business-rule decisions this specification-only phase has no authority to make (which fee schedule, whose accounting policy). If InfinityForge needs net revenue or fee-adjusted figures as a *raw* fact (rather than a downstream calculation), that is a candidate for explicit review via `CONTRIBUTING.md` — it is not decided here, and no implementation should invent its own interpretation in the meantime.

### 3.2 Ad Impressions

**Definition.** `ad_impression` (`metrics/advertising.yaml`) — one advertisement actually shown to and measured as viewed by the user.

**The "actually measured" distinction.** An impression must represent the source ad system's own confirmed impression-counting moment — never an ad *request*, an ad *load*, or an ad-containing screen being *opened*. Those are three different, earlier points in an ad's lifecycle, each of which can occur without the user ever actually seeing the ad (the request can fail, the load can complete without display, the screen can open and close before rendering). Recording any of those as `ad_impression` would inflate impression counts relative to what the ad system itself reports, breaking the eCPM calculation this metric exists to support (`derived-metrics.md`) and any provider reconciliation. If an implementation wants to separately track request/load/open-level funnel behavior, that is an application-specific event (`conventions.md`), not this metric.

**Purpose.** The raw count of realized ad exposure — the impression-side input to eCPM, alongside `ad_revenue`.

**Required fields.** `unit` is fixed to `impression`; `value` is `1` per measurement (see `metrics/advertising.yaml`).

**Optional fields.** `dimensions.placement`, `dimensions.ad_format`, `dimensions.network`.

**Example.** `examples/metrics/ad_impression.json`.

**Validation rules.** `value` must equal `1` for this metric (enforced by `validation/validate.py`, since this metric's definition fixes it — see section 9).

**Versioning implications.** Standard metric `schema_version` model (section 11).

**Privacy considerations.** `dimensions.network`/`placement` must be stable identifiers, never a value that could identify an individual user or their content.

**Provider implementation guidance.** An ad mediation/network SDK typically exposes an impression-level callback; that is the correct trigger point. `docs/implementation-guide.md` covers provider adapter responsibility for translating a provider's own impression event into this shape without leaking provider-specific structure into the normalized measurement.

### 3.3 Ad Revenue

**Definition.** `ad_revenue` (`metrics/advertising.yaml`) — a monetary value attributed to advertising, as reported by the advertising source.

**Purpose.** The monetary counterpart to `ad_impression` — together they support eCPM (`derived-metrics.md`).

**Required fields.** `unit` is fixed to `currency`, so `currency` is required.

**Optional fields.** `dimensions.placement`, `dimensions.ad_format`, `dimensions.network`, `dimensions.precision` (`exact` / `estimated` — many ad mediation systems report modeled, not exactly-known, per-impression revenue; this dimension lets that distinction survive into the data rather than being silently presented as exact).

**Example.** `examples/metrics/ad_revenue.json`.

**Validation rules.** Same currency/value rules as any `unit: currency` metric (section 9).

**Versioning implications.** Standard metric `schema_version` model (section 11).

**Privacy considerations.** Same as 3.2.

**Provider implementation guidance.** Provider adapters may receive this data from provider-specific callbacks — directly per-impression, or estimated/aggregated by the provider itself. Whichever shape the provider gives it in, the normalized `ad_revenue` measurement this contract defines carries no provider-specific structure; that translation is entirely the adapter's responsibility (`docs/implementation-guide.md`), consistent with this contract naming no advertising vendor anywhere in `specification/`, `metrics/`, or `schema/`.

### 3.4 Purchases

**Definition.** The raw purchase fact is `purchase_completed` (`events/monetization.yaml`) — unchanged by this phase except for the addition of an optional `transaction_id` property (see section 3.1). This phase does not introduce a separate "purchase" metric.

**How purchase facts differ from generic revenue measurements.** `purchase_completed` describes a specific **business occurrence**: a one-time purchase completed, for a specific `product_id`, optionally with `price`/`currency`/`quantity`. `revenue` (3.1) is the normalized, source-agnostic **monetary measurement** — usable whether the money came from that purchase, a subscription charge, a renewal, or a refund. A purchase without an accompanying `revenue` measurement is still a complete, valid `purchase_completed` event (the event doesn't require `price`); a `revenue` measurement without an accompanying purchase event is valid too (for example, revenue from a subscription renewal, which has no discrete event). Applications that want both — the descriptive business record and the normalized monetary fact — emit both, linked by `transaction_id`/`reference_id`.

**Required/optional fields, example, validation, versioning, privacy.** See `events/monetization.yaml`'s `purchase_completed` definition and `events.md`/`versioning.md`/`privacy.md` — unchanged by this phase, aside from the additive `transaction_id` property.

**Provider implementation guidance.** No change from existing guidance — a billing/store provider adapter maps its own purchase-confirmation callback onto `purchase_completed`, and may additionally emit a `revenue` measurement for the same transaction.

### 3.5 Subscriptions

**Definition.** The raw subscription facts are `subscription_started` and `subscription_cancelled` (`events/monetization.yaml`) — unchanged by this phase except for the addition of an optional `transaction_id` property on each.

**How subscription facts feed downstream calculations.** `subscription_started`/`subscription_cancelled` (business occurrences) combined with `revenue` measurements (3.1, for the recurring charges themselves — initial and renewal) are the underlying facts for MRR, ARR, churn, conversion, and LTV — see `derived-metrics.md` for exactly how. This contract does not emit any of those derived values directly (section 2C).

**Trial.** `trial_started` (`events/monetization.yaml`) already exists and is unchanged.

**Renewal.** This contract does not currently define a `subscription_renewed` event. A renewal charge is represented as a `revenue` measurement (`dimensions.transaction_type: charge`, `dimensions.billing_type: subscription`) with no accompanying event — see the decision log entry below.

**Required/optional fields, example, validation, versioning, privacy.** See `events/monetization.yaml`'s definitions — unchanged aside from the additive `transaction_id` property.

**Provider implementation guidance.** No change from existing guidance.

**Decision log.** Whether InfinityForge should add a `subscription_renewed` event (so that renewal is as explicitly modeled as start/cancel) is a genuine, reasonable extension this phase deliberately does **not** make: it is an EVENT-taxonomy decision, not a Metrics/Telemetry one, and the existing `revenue` measurement already gives downstream systems what they need to calculate MRR/ARR without it. If a future need for an explicit renewal *event* (as opposed to the revenue fact) arises, propose it via `CONTRIBUTING.md` against `events/monetization.yaml` directly.

### 3.6 Engagement

**Definition.** `session_duration` (`metrics/engagement.yaml`) — the length of one completed session. This is the only new engagement metric this phase adds; session/screen/feature *occurrence* is already fully covered by `app_opened`, `screen_viewed`, and `feature_used` (`events/application.yaml`, `events/product.yaml`).

**Raw observations vs. derived values.** `session_duration`, and the occurrence counts already available from `app_opened`/`screen_viewed`/`feature_used`, are the raw observations. DAU, WAU, MAU, and engagement rate are derived from *counting distinct users* across those raw observations over a window — this contract does not define a session boundary, and does not emit DAU/WAU/MAU/engagement rate itself. See `derived-metrics.md`.

**Required/optional fields.** No dimensions are defined for `session_duration`; `unit` is fixed to `second`.

**Example.** `examples/metrics/session_duration.json`.

**Validation rules.** Standard envelope + non-negative-value rules (section 9).

**Versioning implications.** Standard metric `schema_version` model (section 11).

**Privacy considerations.** None beyond the general rules — `session_duration` carries no identifying content by construction.

**Provider implementation guidance.** This contract does not define what constitutes a session boundary (foreground/background transitions, an inactivity timeout, or another application-specific rule) — that is left to the implementation, applied consistently, exactly as `screen-tracking.md` leaves screen-boundary detection to the application.

### 3.7 Performance

**Definition.** `app_launch_duration`, `screen_load_duration`, and `operation_duration` (`metrics/performance.yaml`). `app_launch_duration` and `screen_load_duration` are named separately because they are foundational, near-universal measurements; every other timing (API latency, network timing, storage/database timing, or any other measurable operation) is unified under the single, generic `operation_duration`, disambiguated by its required `dimensions.operation` — this keeps the taxonomy small (`metric-taxonomy.md`) while remaining fully extensible to any operation an implementation wants to time, without adding a new canonical metric per operation kind.

**Purpose.** App-launch and screen-load performance are foundational product-quality signals; `operation_duration` gives implementations one consistent way to measure everything else, comparable across releases because the shape never changes even as the set of measured `operation` values grows.

**Required fields.** `app_launch_duration`/`screen_load_duration`/`operation_duration` all fix `unit` to `millisecond`. `screen_load_duration` requires `dimensions.screen_name`; `operation_duration` requires `dimensions.operation`.

**Optional fields.** `app_launch_duration.dimensions.launch_type` (`cold`/`warm` — the same distinction `app_opened.launch_type` uses); `operation_duration.dimensions.operation_category` and `.outcome`.

**Example.** `examples/metrics/app_launch_duration.json`, `examples/metrics/screen_load_duration.json`, `examples/metrics/operation_duration.json`.

**Validation rules.** Standard envelope rules, plus the required-dimension rules above (section 9).

**Versioning implications.** Standard metric `schema_version` model (section 11).

**Privacy considerations.** `dimensions.operation` must be a stable, logical identifier (`"api:get_profile"`) — never a value containing personal information, a raw URL with query parameters, or free text, per the same rule `screen-tracking.md` applies to `screen_name`.

**Provider implementation guidance.** This contract names no performance-monitoring SDK or vendor. Whatever instrumentation an implementation uses internally to obtain these durations is entirely its own choice; only the resulting normalized shape is governed here.

### 3.8 Reliability / Errors

**Definition.** `handled_error` (`metrics/reliability.yaml`) — one occurrence of an error or operational failure the application detected and handled (i.e., did not crash from).

**The recoverable/operational/crash distinction.** This contract distinguishes exactly two categories, via the required `dimensions.category`:

- **`recoverable_error`** — an application-level error the app recovered from in the normal course of handling it.
- **`operational_failure`** — a failure of some operation the app depends on (a network request, a storage read/write, a third-party call).

**Crashes are explicitly out of scope.** This contract defines no crash category, no crash event, and no crash-reporting contract of any kind in this phase. Crash capture (stack traces, native symbolication, and similar) is a fundamentally different mechanism with its own provider-specific tooling; folding it into this metric, or inventing a parallel vendor-neutral crash contract, is not attempted here. An implementation that wants crash reporting uses whatever mechanism it already has for that, entirely outside this contract.

**Purpose.** Raw reliability signal — how often, and in what category, handled errors and operational failures occur. Aggregation (counts per window, per category) is a downstream calculation over these raw `value: 1` measurements, consistent with how `ad_impression` and other count-shaped metrics work.

**Required fields.** `dimensions.category` (`recoverable_error` / `operational_failure`).

**Optional fields.** `dimensions.error_code` — a stable, application-defined code, never a free-form message or stack trace.

**Example.** `examples/metrics/handled_error.json`.

**Validation rules.** `dimensions.category` present and one of the two allowed values (never a third, undocumented value meaning "crash" — section 9).

**Versioning implications.** Standard metric `schema_version` model (section 11).

**Privacy considerations.** `error_code` must never contain a raw exception message, stack trace, file path, or any value that could carry personal information — `privacy.md`'s metrics-specific section makes this explicit.

**Provider implementation guidance.** None — this is intentionally provider-agnostic and does not correspond to any specific crash/error-reporting vendor's data model.

### 3.9 Notifications

**Evaluation.** Notification-related measurements (`notification_sent`, `notification_delivered`, `notification_opened`) were evaluated against this phase's scope and **are not added** as canonical Metrics.

**Why.** Each of these is structurally a discrete, nameable delivery-state **occurrence** — "a notification reached state X" — not a value-plus-unit measurement. That shape fits the **Event** primitive (section 2A), not the **Metric** primitive this phase defines. Adding new canonical Events is a decision about extending `events/*.yaml`'s taxonomy, which this Metrics/Telemetry phase does not have a mandate to do on its own judgment (`contract.md`'s "do not redesign the existing event/identity contract unnecessarily").

**The distinction, documented for future work.** If a future phase adds notification events, the same raw-vs-derived principle applies: `notification_sent`/`delivered`/`opened` would be provider-delivery **facts**; a "notification conversion rate" or "notification-attributed engagement" would be a **derived metric** (section 2C / `derived-metrics.md`), calculated downstream from those facts and never emitted directly.

**What this means today.** No notification event or metric exists in this contract. An application that wants to track notification delivery today may use an app-specific event (`conventions.md`, `events.md`'s "common vs. app-specific" distinction) until/unless this is formally added to the canonical taxonomy via `CONTRIBUTING.md`.

### 3.10 Attribution / Acquisition

**Evaluation.** Acquisition/attribution data (source, campaign, medium, and similar attribution context) was evaluated and is modeled as **dimensions on relevant metrics/events**, not as an independent metric or event.

**Why.** Attribution context describes *where a user, session, or transaction came from* — it decorates another fact (a `revenue` measurement, a `subscription_started` event) rather than being a fact on its own. Step 6's dimensions/context model (`metric-envelope.md`) already exists for exactly this. Making it a standalone metric would invite exactly the "unbounded, ungoverned bag of data" problem `metric-envelope.md`'s dimensions section explicitly guards against, since attribution values (campaign names, source identifiers) are naturally high-cardinality and provider-specific.

**What this contract does not do.** It does not assume any particular attribution provider or model, and does not currently define standard attribution dimension names on any canonical metric (no canonical metric in `metrics/*.yaml` includes an `acquisition_source`/`campaign` dimension today) — no canonical metric in this phase has an acquisition-adjacent use case strong enough to justify one. An application that needs to attach attribution context to a metric or event today does so via app-specific dimensions/properties, following `conventions.md` and `privacy.md`. If InfinityForge later wants a **canonical** `acquisition_source`/`campaign`/`medium` dimension shared across multiple metrics, that is a well-defined, minimal future addition — not introduced here without a concrete need driving its exact shape.

### 3.11 Conversion

**No generic conversion metric.** This contract does not define a `conversion` metric or event. Conversion rate is, in every case, a ratio between two counts of existing facts already defined by this contract — for example, `signup_started` vs. `signup_completed`, `paywall_viewed` vs. `subscription_started`/`purchase_completed`, or `trial_started` vs. `subscription_started`. See `derived-metrics.md`'s conversion row for the general pattern.

## 4. Deduplication and idempotency

Purchases, subscription lifecycle changes, ad impressions, and ad revenue are the measurement classes most likely to need deduplication — a network retry, a provider callback firing more than once, or an offline queue replaying a measurement. This contract addresses this at the **contract level only**, per the instruction not to invent provider behavior:

- **`reference_id`** (`metric-envelope.md`) is the standard, optional field for a stable, source-system identifier a metric can be deduplicated on, when the source system provides one (a provider-issued impression ID, a payment transaction ID).
- **`transaction_id`** (added to `purchase_completed`, `subscription_started`, `subscription_cancelled` in this phase) serves the same purpose for events, and is the natural value to also use as the accompanying `revenue` measurement's `reference_id` (section 3.1).
- This contract does not mandate that every measurement carry a `reference_id` — many legitimately don't have a natural one (`session_duration`, `handled_error`). Where one is available, an implementation should supply it; where a metric class genuinely needs reliable deduplication and its source system provides no stable identifier, that is a limitation of the source system this contract cannot resolve, not something an implementation should invent a synthetic identifier to paper over.
- Actual deduplication logic (whether to drop a duplicate `reference_id`, at what layer) is a transport/storage concern, deliberately left to the implementation or downstream ingestion system — the same boundary `contract.md` already draws for events ("Transport... is not specified").

## 5. Sampling and frequency

This contract does not prescribe sampling, batching, or aggregation-before-transmission mechanics — those are transport optimizations, and `contract.md` already leaves transport entirely to implementations. What it does say, semantically:

- A high-frequency metric (for example, `operation_duration` measured on every single network call in a busy app) may legitimately be sampled by an implementation for volume/cost reasons, **as long as** the implementation does not misrepresent a sampled subset as a complete measurement set to a consumer that assumes otherwise — this is a documentation/communication concern for the implementation, not something this contract can enforce structurally.
- This contract does not require or forbid pre-aggregating multiple raw occurrences into a single emitted measurement (for example, batching ten `ad_impression` measurements from the same placement within a short window into one metric with `value: 10`). Where a canonical metric's definition fixes `value` to a specific meaning (`ad_impression`'s `value` is always `1` — section 3.2), an implementation must not silently repurpose it to mean "count of a batch" instead — that would violate the metric's documented shape. A metric that genuinely wants to represent a pre-aggregated count should be a distinct, explicitly-defined metric (not introduced in this phase, since none of the eight canonical metrics here call for it), not a repurposing of an existing one.

## 6. Offline and retry semantics

Identical boundary to events (`contract.md`): this contract does not specify how a measurement is queued, retried, or delivered while the device is offline, and does not prescribe a storage or queue mechanism. What carries over from the event model unchanged:

- A metric's `timestamp` is captured at the moment the measurement was recorded, not at the moment it is eventually transmitted (`metric-envelope.md`) — this must hold even if transmission is delayed by offline queuing.
- Error-handling rules (`errors.md`, extended for metrics in that document's own metrics subsection) apply identically: a metric that cannot currently be transmitted must never crash the app or block a user-facing action; it may be corrected, dropped, or queued, in that order of preference.
- Retried/replayed delivery is exactly the scenario `reference_id` (section 4) exists to make deduplicable when the source system provides one.

## 7. Provider independence

Metrics follow the identical adapter model events already do (`docs/implementation-guide.md`, `overview.md`):

```
Application
    |
InfinityForge contract (Event + Metric primitives)
    |
Platform implementation
    |
Provider adapter
    |
Provider
```

A provider may directly support a given metric, represent it under a different native concept, require multiple calls to assemble it, or not support it at all. None of that changes what the metric *means* once normalized into this contract's shape — provider limitations belong in a platform adapter's own implementation documentation, never in this normative specification, unless a limitation is truly universal across every conceivable provider (in which case it would already be reflected in how the metric itself is defined here, as `ad_revenue`'s optional `precision` dimension already accounts for the universal reality that ad revenue attribution is sometimes estimated).

## 8. Cross-platform interoperability

Exactly as `contract.md` requires for events: nothing in this document, `metric-envelope.md`, `metric-taxonomy.md`, `derived-metrics.md`, `metrics/*.yaml`, `schema/metric-envelope.yaml`, or `schema/metric-dimensions.yaml` references React Native, Swift, Kotlin, or any other platform-specific API. Examples throughout use only the normalized envelope shape. A React Native, Swift, or Kotlin implementation — or a future platform's — reads these documents and builds a conforming adapter without needing to look at any other platform's code, exactly as `overview.md` already states as a design goal for the contract as a whole.

## 9. Validation rules

A metric is malformed under the same general definition `errors.md` already uses for events, extended with metric-specific conditions (also documented in `errors.md`'s own metrics subsection):

- a required envelope field is missing, empty, or the wrong type (`schema/metric-envelope.yaml`)
- `metric_name` is not `snake_case`, or does not match a documented canonical metric name (`metrics/*.yaml`) or a valid app-specific metric name (`conventions.md`)
- `value` is missing, not a number, or negative
- `unit` is missing or not one of the allowed values (`schema/common-types.yaml#/$defs/metric_unit`)
- `unit` is `currency` and `currency` is absent, or `unit` is not `currency` and `currency` is present
- `source` is missing or not one of the allowed values (`schema/common-types.yaml#/$defs/metric_source`)
- a dimension marked `required: true` on the metric's definition is missing
- a dimension's value does not match its documented `type`, or (for `type: enum`) is not among its `allowed_values`
- a dimension key collides with a reserved envelope field name, or is not `snake_case`
- `schema_version` is missing or not a positive integer

**What happens when validation fails.** Identical philosophy to events (`errors.md`): correct what can be unambiguously corrected, or drop the offending measurement and continue, or queue it for later resolution — in that order of preference. A malformed metric must never surface as an exception the calling application must handle, exactly as for a malformed event.

## 10. Privacy

See `privacy.md`'s dedicated metrics subsection for the full extension of the existing privacy rules to `value`, `dimensions`, `source`, and `reference_id`. In summary: every prohibited data category already defined for events applies identically to metrics, with two metric-specific emphases — dimensions must stay low-cardinality and categorical (never raw free text or per-user unique values), and `reference_id`/error-adjacent dimensions must be opaque identifiers or stable codes, never raw transaction/payment data or exception message text.

## 11. Versioning

See `versioning.md`'s dedicated "Metric schema_version" section (added in this phase, mirroring the existing "App-specific event schema_version" section exactly). In summary: a metric's `schema_version` follows the identical three-level model events already use (contract version in `CHANGELOG.md`, per-metric `schema_version` in `metrics/*.yaml`, `sdk_version` in the envelope), and an app-specific metric's `schema_version` is owned by the application that defines it, exactly as for an app-specific event.
