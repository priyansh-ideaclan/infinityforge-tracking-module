# Metric Taxonomy

This document lists the canonical metrics this contract currently defines, organized by category, mirroring how `events.md` organizes the event taxonomy. The metric definitions themselves are machine-readable YAML files under `metrics/`, one file per category — see `specification/metrics.md` for the full semantic definition of each, and `specification/metric-envelope.md` for the envelope fields every metric shares.

This is a deliberately **small** taxonomy. A metric is added here only when it is a genuinely new raw measurement with no existing home in the event taxonomy — see `specification/metrics.md` for the reasoning behind each inclusion (and each deliberate exclusion — attribution, conversion, and notifications are evaluated in `metrics.md` but do not have entries here; see sections 3.9–3.11).

## Categories

| Category | File | Metrics |
|---|---|---|
| Monetization | `metrics/monetization.yaml` | `revenue` |
| Advertising | `metrics/advertising.yaml` | `ad_impression`, `ad_revenue` |
| Engagement | `metrics/engagement.yaml` | `session_duration` |
| Performance | `metrics/performance.yaml` | `app_launch_duration`, `screen_load_duration`, `operation_duration` |
| Reliability | `metrics/reliability.yaml` | `handled_error` |

## Summary table

| Metric | Category | Unit | Typical source | Currency? | Key dimensions |
|---|---|---|---|---|---|
| `revenue` | Monetization | `currency` | `billing_system` | Required | `transaction_type` (required), `billing_type`, `product_id` |
| `ad_impression` | Advertising | `impression` | `advertising_system` | — | `placement`, `ad_format`, `network` |
| `ad_revenue` | Advertising | `currency` | `advertising_system` | Required | `placement`, `ad_format`, `network`, `precision` |
| `session_duration` | Engagement | `second` | `application` | — | none |
| `app_launch_duration` | Performance | `millisecond` | `application` | — | `launch_type` |
| `screen_load_duration` | Performance | `millisecond` | `application` | — | `screen_name` (required) |
| `operation_duration` | Performance | `millisecond` | `application` | — | `operation` (required), `operation_category`, `outcome` |
| `handled_error` | Reliability | `count` | `application` | — | `category` (required), `error_code` |

## How a metric is documented

Every entry in `metrics/*.yaml` includes:

| Field | Meaning |
|---|---|
| `name` | The canonical metric name, `snake_case` |
| `description` | What the metric represents |
| `trigger` | The condition under which it should be recorded |
| `purpose` | Why this metric exists — what question it lets someone answer, and which derived metric(s) it feeds (see `derived-metrics.md`) |
| `schema_version` | This metric's own schema version — identical rule to an event's `schema_version` (`versioning.md`) |
| `unit` | The fixed unit this metric's `value` is expressed in (`metric-envelope.md`) |
| `typical_source` | The `source` value implementations should typically use for this metric — guidance, not a hard per-instance lock (`metric-envelope.md`) |
| `dimensions` | The list of documented dimensions (see below) |
| `example` | A path to a full example payload under `examples/metrics/` |

Each entry in `dimensions` follows the shape defined in `schema/metric-dimensions.yaml`: `name`, `type`, `required`, `description`, and — for `type: enum` — `allowed_values`.

## Common dimensions vs. app-specific dimensions

Every dimension listed inside `metrics/*.yaml` is part of the contract, with an agreed meaning across every InfinityForge app and platform — the metric counterpart to an event's common properties (`events.md`). Applications may additionally send app-specific dimensions on any metric, under the same rules app-specific event properties follow: `conventions.md` naming/typing, `privacy.md` compliance, no reuse of a common dimension's name with a different meaning, and no cross-app compatibility guarantee.

## Category boundaries

- **Monetization** covers monetary value realized (`revenue`). It does not duplicate the existing monetization **events** (`events/monetization.yaml`) — `paywall_viewed`, `trial_started`, `subscription_started`, `subscription_cancelled`, and `purchase_completed` remain the canonical record of a monetization business occurrence. See `metrics.md` section 3.1/3.4/3.5 for the full relationship.
- **Advertising** covers ad exposure and ad-attributed revenue — a category this contract had no prior coverage of at all.
- **Engagement** covers only the raw measurement gap not already covered by existing engagement-adjacent events (`app_opened`, `screen_viewed`, `feature_used`) — session length. It does not include DAU/WAU/MAU or engagement rate; those are derived (`derived-metrics.md`).
- **Performance** covers operation timing, generically, per `metrics.md` section 3.7.
- **Reliability** covers handled errors and operational failures only — explicitly not crashes. See `metrics.md` section 3.8.

## Adding a new metric

New metrics are added through the same process `CONTRIBUTING.md` defines for events, with a metrics-specific checklist added there. A metric is added only when the underlying measurement has no reasonable home as an existing event, or as a dimension on an existing metric — the taxonomy stays intentionally small.
