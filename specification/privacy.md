# Privacy Rules

These rules are platform-independent and apply to every event, every property, every metric, every dimension, and every user-level attribute set through this contract, regardless of which adapter or analytics provider ultimately receives the data.

## Prohibited data categories

The following must **never** appear in an event property, a user property, an event name, a screen name, or any other value passed through this contract:

- passwords, passphrases, or password hints
- authentication tokens, session tokens, refresh tokens, or API keys
- payment card data (card numbers, CVV/CVC, expiry, or any other PAN-adjacent data)
- private keys, cryptographic secrets, or credentials of any kind
- unnecessary sensitive personal information — including but not limited to government-issued identification numbers, precise home addresses, health information, or other data not clearly required for the event's documented purpose

This list is a floor, not a ceiling. When in doubt about whether a value is sensitive, do not track it.

## General principle

Event and user properties should describe **behavior and state**, not **identity or sensitive content**. A property should answer "what happened" or "what is true about this user's configuration or cohort," not carry free-form personal content. Prefer stable identifiers, categories, and enums over raw personal data — for example, a `plan` property identifying a subscription tier is appropriate; a property containing a user's full name or email address is not.

## Review and approval for exceptional data

If a genuinely justified need arises to collect something that could be considered sensitive personal information, it must go through explicit review and be documented as an approved exception in this repository (via the change process in `CONTRIBUTING.md`) **before** any implementation collects it. The default is that such data is not collected; an undocumented exception is not a valid exception, regardless of the application's own justification.

## Scope of these rules

These rules apply equally to canonical events (`events/*.yaml`) and to app-specific events and properties that applications add on top of this contract. Being outside the canonical taxonomy does not exempt a property from these rules.

## Metrics and dimensions

Everything above applies to a metric's `dimensions` exactly as it applies to an event's `properties` — the prohibited data categories, the "behavior and state, not identity or sensitive content" principle, and the exceptional-data review process all carry over unchanged. This section adds the rules specific to the metric shape introduced in this phase (`specification/metrics.md`, `specification/metric-envelope.md`).

- **Dimension cardinality.** A dimension's allowed types are already restricted to `string`, `integer`, `boolean`, and `enum` (`schema/metric-dimensions.yaml`), and a dimension's value must be a bounded, low-cardinality category — never free text, and never a value whose cardinality approaches the number of users or events (a raw identifier, a timestamp-derived string, a user-entered string). A `string`-typed dimension is for a bounded label (a placement name, an operation name) drawn from a small, application-controlled set — not an open text field. Where a dimension's set of valid values is small and fixed, `enum` is preferred over `string` specifically because it is easier to audit for accidental high-cardinality or sensitive content.
- **`reference_id` opacity.** `reference_id` (`schema/metric-envelope.yaml`) must be an opaque identifier — a transaction ID, an order ID, or similar handle meaningful only for correlating a metric back to its source system or to a related event's `transaction_id`. It must never itself carry personal information (for example, it must not be a concatenation that embeds an email address or a name) and must never be a payment card or account number.
- **`error_code` opacity.** `handled_error`'s `error_code` dimension (`metrics/reliability.yaml`) must be a stable, application-defined error category or code (for example, `sync_conflict`, `E_TIMEOUT`) — never a raw exception message, stack trace fragment, or free-form string that could incidentally contain user data. A raw message belongs in server-side or crash-reporting tooling outside this contract's scope (`specification/metrics.md` section 3.8), not in a tracked dimension.
- **No monetary precision leak.** `revenue` and `ad_revenue`'s `value` (`specification/metric-envelope.md`) is a measurement of a transaction amount, not a place to encode anything beyond that amount — implementations must not, for example, encode a per-user discount code or promotional identifier into `value` or into a dimension in a way that narrows a monetary figure down to an identifiable individual transaction pattern beyond what `reference_id` already exists to carry.
- **Review and approval.** The same exceptional-data review process (above) governs any proposed metric or dimension that might touch a prohibited data category — there is no separate, lighter-weight review path for metrics.

## What this document does not claim

This document defines InfinityForge's own internal data-minimization rules. It does not, by itself, constitute or guarantee compliance with any specific privacy law or regulation (such as GDPR, CCPA, or others) in any jurisdiction. Teams building on this contract remain responsible for determining and meeting their own regulatory obligations; following these rules is necessary but not automatically sufficient for that purpose.
