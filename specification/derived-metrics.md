# Derived Metrics

This is the dedicated normative section (`metrics.md` section 2 refers here) for the rule that governs every derived business/analytics metric: **a derived metric is a downstream calculation, never a client tracking fact.**

## The rule

A conforming implementation must **not** emit any of the derived metrics listed below — or any other value calculated from a collection of events/measurements rather than observed directly at a single point in time — as if it were a raw event or metric. Nothing in this contract prevents a downstream system (an analytics warehouse, a BI tool, a reporting service) from *calculating* these values from the raw facts this contract does define; what this contract governs is only what a platform SDK running on a user's device may record and transmit, and a derived metric is, by definition, not something observable at a single point on a single device — it requires aggregation across users, sessions, or time that only a downstream system has visibility into.

This is the same principle `events.md` and `metrics.md` already apply consistently: the contract records **facts and raw measurements**; everything calculated from a collection of them is out of scope for what an SDK emits.

## Why this matters

If a derived metric were emitted as a tracking fact, two implementations could disagree about how it was calculated (which cohort window, which timezone, whether a refunded purchase counts) while both appearing to emit "the same" field — silently producing incomparable data across platforms, which is exactly what this contract exists to prevent (`contract.md`'s cross-platform guarantees). Keeping calculation entirely downstream means there is exactly one definition of, say, "churn" for a given analysis, decided once by whoever runs that calculation, rather than N slightly-different definitions baked into N platform SDKs.

## Derived metrics and their underlying facts

For each metric below: the raw facts required to calculate it, and where this contract defines them. This is documentation of the calculation's *inputs*, not a formula this contract mandates a specific implementation of — the exact windowing, timezone, and cohort rules are downstream decisions.

| Derived metric | Underlying facts | Defined in |
|---|---|---|
| **DAU / WAU / MAU** (daily/weekly/monthly active users) | Distinct `anonymous_id`/`user_id` values observed on events (typically `app_opened`, or any event) within the window | `events/application.yaml`, `identity.md` |
| **Retention** | A cohort's initial activity (for example, `signup_completed` or first `app_opened`) plus that same cohort's subsequent activity in later windows | `events/authentication.yaml`, `events/application.yaml`, `identity.md` |
| **Engagement rate** | Active-user counts (as for DAU/MAU) relative to a defined eligible population | `events/application.yaml` |
| **MRR** (monthly recurring revenue) | Active subscription state (`subscription_started` / `subscription_cancelled`) combined with `revenue` measurements for those subscriptions, normalized to a monthly period | `events/monetization.yaml`, `metrics/monetization.yaml` |
| **ARR** (annual recurring revenue) | MRR, annualized | Derived from MRR, above |
| **Churn** | Subscription lifecycle facts — `subscription_started`, `subscription_cancelled`, and renewal-adjacent `revenue` measurements (or their absence) over a cohort window | `events/monetization.yaml`, `metrics/monetization.yaml` |
| **LTV** (lifetime value) | `revenue` measurements (all `transaction_type` values) attributed to a `user_id`/`anonymous_id` over its full observed lifecycle, combined with subscription/purchase lifecycle facts | `metrics/monetization.yaml`, `events/monetization.yaml`, `identity.md` |
| **ARPU** (average revenue per user) | `revenue` measurements over a window, divided by an active-user count (as for DAU/MAU) over the same window | `metrics/monetization.yaml`, `events/application.yaml` |
| **ARPPU** (average revenue per paying user) | Same as ARPU, with the denominator restricted to users with at least one `subscription_started`/`purchase_completed`/qualifying `revenue` measurement in the window | `metrics/monetization.yaml`, `events/monetization.yaml` |
| **eCPM** (effective cost per mille) | `ad_revenue` divided by `ad_impression` count, scaled to a thousand impressions | `metrics/advertising.yaml` |
| **ROAS** (return on ad spend) | `revenue` (or `ad_revenue`, depending on the analysis) attributed to a cohort, divided by acquisition spend/cost data for that cohort — this contract defines no acquisition **spend** fact; see section 3.10 in `metrics.md` for why acquisition cost data is out of scope here | `metrics/monetization.yaml`; acquisition spend is external to this contract |
| **Conversion rate** (any funnel: signup, trial, subscription, purchase) | The count of qualifying "entry" events divided by the count of qualifying "completion" events over the same window — for example, `signup_started` vs. `signup_completed`, or `paywall_viewed` vs. `subscription_started`/`purchase_completed` | `events/authentication.yaml`, `events/monetization.yaml` |

## What this contract deliberately does not define

- **Cohort/window definitions** (calendar day vs. rolling 24 hours, which timezone, how a "month" is bounded for MRR) — a downstream analysis decision.
- **Net revenue, fee schedules, or accounting adjustments** beyond the raw `transaction_type` distinction on `revenue` (`metric-envelope.md`) — see `metrics.md` section 3.1's decision log entry.
- **Acquisition spend/cost data** — this contract has no client-side visibility into advertising spend; ROAS's cost side is necessarily external.
- **Any specific attribution model** for crediting a conversion or a revenue event to an acquisition source — see `metrics.md` section 3.10.

If a future need arises for this contract to define one of these more precisely (for example, because two platform teams have started calculating the same derived metric incompatibly and need a shared definition to converge on), that is a candidate for a future, separately-reviewed extension — not something this phase resolves.
