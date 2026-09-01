# Metric Envelope

Every metric (raw measurement) recorded through this contract carries a fixed set of fields — the **metric envelope**, defined machine-readably in `schema/metric-envelope.yaml`. This document is the metric counterpart to `metadata.md`: it explains what each field means, who supplies it, and — for the fields unique to a metric rather than an event — the value, unit, currency, source, and dimension rules that govern them.

This document does not redefine anything `metadata.md` or `identity.md` already define. Every identity and application-metadata field below (`app_id`, `environment`, `platform`, `sdk_name`, `sdk_version`, `app_version`, `user_id`, `anonymous_id`, `timestamp`) is the exact same field, with the exact same meaning, ownership, and rules, as its counterpart on the event envelope. A metric recorded at the same moment as an event carries identical values for all of these.

## Field ownership

| Field | Supplied by | Notes |
|---|---|---|
| `metric_name` | Application/SDK | The canonical or app-specific metric name, per the metric definition being emitted (`metrics/*.yaml`). |
| `schema_version` | SDK | The `schema_version` of the metric definition being emitted. Same rules as an event's `schema_version` — see `versioning.md`. |
| `value` | Application/SDK | The measured numeric value, in `unit`. See "Value and unit semantics" below. |
| `unit` | Fixed by the metric definition | Not chosen per-call — every emission of a given `metric_name` uses the unit its definition specifies. |
| `currency` | Application/SDK | Required when `unit` is `currency`; must not be present otherwise. |
| `source` | Application/SDK | The general category of system that produced the measurement. See "Source semantics" below. |
| `reference_id` | Application/SDK, from the source system, when available | Optional. See "Deduplication" in `metrics.md`. |
| `timestamp` | SDK | Captured automatically at the moment the measurement is recorded. Identical rule to the event envelope. |
| `app_id`, `environment`, `platform`, `sdk_version`, `sdk_name`, `app_version` | Same as event envelope | See `metadata.md` — unchanged. |
| `user_id`, `anonymous_id` | SDK, from identity state | Identical rule to the event envelope — see `identity.md`. A metric recorded while a user is identified carries the same `user_id` an event would. |
| `dimensions` | Application/SDK | Metric-specific contextual key-value pairs. See "Dimensions" below. |

No field is supplied directly by a backend at capture time — same rule as the event envelope (`metadata.md`).

## Value and unit semantics

`value` is always a non-negative decimal number (`schema/common-types.yaml#/$defs/metric_value`) — a magnitude, never a signed quantity. `unit` (`schema/common-types.yaml#/$defs/metric_unit`) is fixed per metric definition and determines what `value` means:

| `unit` | `value` represents | Requires `currency` |
|---|---|---|
| `currency` | A monetary amount, in the currency's major unit — identical convention to an event's `price` property (`conventions.md`): `4.99`, never `499` minor units, never a currency symbol. | Yes |
| `count` | A whole-number tally of occurrences of whatever the metric measures (typically `1` per measurement — see the individual metric definition for whether it represents one occurrence or a pre-aggregated total). | No |
| `impression` | The number of ad impressions this measurement represents (see `metrics.md` section 3.2 — currently always `1`). | No |
| `millisecond` / `second` | A duration, in the named unit. An implementation must use the unit the metric definition specifies — it must not, for example, emit `app_launch_duration` in seconds because that happens to be convenient; convert before emitting. | No |
| `other` | Reserved for a unit not yet enumerated here — see `schema/common-types.yaml`'s note on narrowing it before use at scale. | No |

**Precision and rounding.** This contract does not mandate a specific decimal precision for `value`. An implementation should preserve the precision meaningful to the measurement's source (for example, an ad network's reported revenue may have more decimal places than a `4.99` product price) and must not round in a way that silently discards a materially different value. It must not introduce false precision either — reporting more decimal digits than the source measurement actually supports.

**Representing direction without a signed value.** Some measurements are naturally "negative" in accounting terms — most notably a refund. This contract represents that through a dimension on the specific metric (for example, `revenue`'s `transaction_type` dimension: `charge` / `refund` / `adjustment`), never through a negative `value`. This keeps `value` unambiguous (always "how much," never "which direction") and keeps the direction semantics explicit and validated per metric, rather than relying on every consumer to remember that a negative number means something different for this one field.

**Gross vs. net.** Unless an individual metric's definition says otherwise, `value` for a monetary metric is the **gross** amount recorded by the source system, before any downstream fee, tax, or platform-cut adjustment. This contract does not currently define a net-revenue metric or model platform fee schedules — see `metrics.md` section 3.1 and this phase's decision log for why that is intentionally out of scope rather than silently assumed.

## Currency semantics

Identical to `conventions.md`'s existing rule for event properties: `currency` is an uppercase ISO 4217 three-letter code (`schema/common-types.yaml#/$defs/currency_code`). It is required whenever `unit` is `currency`, and must be absent for every other `unit` — a `count`, `impression`, `millisecond`, or `second` metric never carries a `currency`, because it isn't a monetary value.

## Source semantics

`source` (`schema/common-types.yaml#/$defs/metric_source`) identifies the general **category** of system that produced a measurement — never a specific vendor or product name:

| `source` | Meaning |
|---|---|
| `application` | The application's own code produced the measurement directly (for example, `session_duration`, `app_launch_duration`). |
| `billing_system` | A payment or subscription system confirmed the measurement (for example, `revenue`). |
| `advertising_system` | An advertising SDK or mediation layer reported the measurement (for example, `ad_impression`, `ad_revenue`). |
| `operating_system` | The device operating system supplied the measurement. |
| `network` | A network-layer timing or measurement (for example, an `operation_duration` for an HTTP call). |
| `provider` | A source not covered by the categories above, but still a distinct external system. |
| `other` | Reserved for a source category not yet enumerated here. |

Each canonical metric definition documents its **typical** `source` value as guidance (`typical_source` in `metrics/*.yaml`), but `source` is not hard-locked to a single value per metric name at the schema level — an application may have a legitimate reason to record the same metric from a different source category (for example, an `operation_duration` measured by `network` in one call and `application` in another). What must never happen, per the "Critical Architecture Principles" this contract is built on, is a specific vendor or product name appearing anywhere in `source`, a dimension value, or any other normative field — see `metrics.md` and `docs/implementation-guide.md` for how vendor-specific detail belongs entirely inside a platform adapter, never in the emitted `source` taxonomy itself.

## Dimensions

`dimensions` is the metric counterpart to an event's `properties` — but governed more tightly, per this phase's explicit design goal of keeping dimensions from becoming "an unbounded, ungoverned bag of data":

- **Allowed types.** Only `string`, `integer`, `boolean`, and `enum` (`schema/metric-dimensions.yaml`) — deliberately narrower than an event property's allowed types. No `number`, `timestamp`, `object`, or `array` dimension. A dimension is a context **label**, not a nested measurement or structure; a genuinely separate numeric measurement belongs in its own metric, not folded into another metric's dimensions.
- **Naming.** Same `snake_case` identifier rules as event properties (`conventions.md`).
- **Cardinality.** A dimension's value should be a bounded, low-cardinality category wherever possible (a plan tier, a placement identifier, an ad format) — not a raw, unbounded, per-user or per-event string. High-cardinality dimension values undermine both the privacy goals in `privacy.md`'s metric-specific section and any downstream system's ability to aggregate by them meaningfully.
- **Reserved fields.** A dimension key must not collide with a reserved metric envelope field name: `metric_name`, `schema_version`, `value`, `unit`, `currency`, `source`, `reference_id`, `timestamp`, `app_id`, `environment`, `platform`, `sdk_version`, `sdk_name`, `app_version`, `user_id`, `anonymous_id`, `dimensions`.
- **Identity, not context.** Dimensions are part of what makes a measurement meaningful (for example, `revenue`'s `transaction_type` is required — the measurement cannot be correctly interpreted without it) or optional descriptive context (for example, `placement` on `ad_impression`). A metric's own definition (`metrics/*.yaml`) marks each dimension `required: true`/`false` accordingly, exactly like an event property.
- **Attribution/acquisition context.** Where an application wants to attach acquisition or attribution context (source campaign, medium) to a metric, that is expressed as dimensions on the relevant metric — not as a separate metric or event of its own. See `metrics.md` section 3.10.

## No duplication

Exactly the rule `metadata.md` already states for events: each field carries one, non-overlapping purpose. Identity is only ever expressed through `user_id`/`anonymous_id`; nothing here should be duplicated inside `dimensions`.
