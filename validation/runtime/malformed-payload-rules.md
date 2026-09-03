# Runtime Malformed-Payload Rules

This document is the language-neutral, machine-readable-adjacent statement of what a
conforming InfinityForge Tracking runtime must check on every `track`, `screen`,
`identify`, `setUserProperties`, and `recordMetric` call, and what it must do when a
check fails. It exists so a new platform adapter (or a reviewer comparing two existing
adapters) has one place to check runtime validation behavior against, instead of
re-deriving it from prose scattered across `specification/errors.md`,
`specification/conventions.md`, `specification/privacy.md`, `specification/identity.md`,
and the `schema/*.yaml` files.

**This document invents no new rules.** Every rule below is a restatement of an
existing rule already stated in the files named next to it — see that file for the
authoritative wording if this document and that file ever appear to disagree (that
would be a bug in this document, not a new contract decision).

A companion machine-readable file, `malformed-payload-rules.json`, lists the same
rules with stable `id`s, so an adapter's validator (or its tests) can reference a rule
by id rather than restating its prose.

## How to read this document

Each rule has:
- **Applies to** — `event`, `metric`, or `both`.
- **Trigger** — the condition that makes a payload malformed under this rule.
- **Required runtime behavior** — what a conforming implementation must do when the
  condition is met (per `specification/errors.md`'s ordered preference: correct, then
  drop, then queue — never propagate an exception the caller must handle).
- **Source** — the specification/schema file this rule is derived from.

## 1. Envelope-level rules

### 1.1 Missing or empty required envelope field
- **Applies to:** both
- **Trigger:** a field listed as `required` in `schema/event-envelope.yaml` (event:
  `event`, `schema_version`, `timestamp`, `app_id`, `environment`, `platform`,
  `sdk_version`, `app_version`, `anonymous_id`) or `schema/metric-envelope.yaml`
  (metric: `metric_name`, `schema_version`, `value`, `unit`, `source`, `timestamp`,
  `app_id`, `environment`, `platform`, `sdk_version`, `app_version`, `anonymous_id`) is
  absent, `null`, or an empty string.
- **Required runtime behavior:** the SDK owns every one of these fields itself (see
  `specification/metadata.md` — none is application-supplied at the call site except
  `event`/`metric_name` and, indirectly, `environment`/`app_id`), so this should never
  occur from a correctly wired adapter. If it does (a programming error in the
  adapter), the event/metric must be dropped and a development diagnostic logged —
  never emitted with a missing field, never a crash.
- **Source:** `schema/event-envelope.yaml`, `schema/metric-envelope.yaml`,
  `specification/errors.md` ("a required envelope field is missing, empty, or the
  wrong type").

### 1.2 Wrong-typed envelope field
- **Applies to:** both
- **Trigger:** a present envelope field does not match its documented type/pattern in
  `schema/common-types.yaml` (for example `environment` outside
  `development|preview|production`, `platform` outside `ios|android|web|other`,
  `schema_version` not a positive integer, `event`/`metric_name` not matching the
  `identifier` pattern `^[a-z][a-z0-9_]*[a-z0-9]$`).
- **Required runtime behavior:** same as 1.1 — drop and log a development diagnostic;
  never emit.
- **Source:** `schema/common-types.yaml`, `specification/errors.md`.

### 1.3 `null` anywhere in an emitted payload
- **Applies to:** both
- **Trigger:** any field, property, or dimension value is `null`.
- **Required runtime behavior:** never emit `null`. An optional value that is absent
  must be omitted entirely, not sent as `null`; a required value that would be `null`
  falls under 1.1/2.1/3.1 (missing required field) and must be dropped, not sent as
  `null`.
- **Source:** `specification/conventions.md` ("Null and absent values").

## 2. Event-specific rules (`track`, `screen`)

### 2.1 Missing required canonical property
- **Applies to:** event
- **Trigger:** the event name matches a canonical event in `events/*.yaml`, and a
  property marked `required: true` on that event's definition is absent from
  `properties`.
- **Required runtime behavior:** drop the offending event and log a development
  diagnostic naming the missing property; never emit an event silently missing a
  required property, never raise an exception to the caller.
- **Source:** `specification/errors.md` ("a property marked required on a canonical
  event definition is missing"), `schema/event-properties.yaml`.

### 2.2 Property value does not match its documented type
- **Applies to:** event
- **Trigger:** for a canonical property, the supplied value's runtime type does not
  match the property's declared `type` (`string`, `integer`, `number`, `boolean`,
  `timestamp`, `enum`, `object`, `array` — `specification/conventions.md`). A boolean
  supplied as the string `"true"`/`"false"` or as `0`/`1` is a type mismatch, not a
  valid boolean (`specification/conventions.md` — "Booleans").
- **Required runtime behavior:** if the mismatch is unambiguously correctable (for
  example a numeric string for a documented `integer`/`number` property), correct it;
  otherwise drop the property (or, if the property was required, drop the whole event
  per 2.1) and log a development diagnostic. Never emit a value of the wrong type.
- **Source:** `specification/errors.md`, `specification/conventions.md`.

### 2.3 Enum property value outside the allowed set (emitting)
- **Applies to:** event
- **Trigger:** a canonical `enum`-typed property's value is not among that property's
  documented `allowed_values`.
- **Required runtime behavior:** drop the property (or the event, if the property was
  required) and log a development diagnostic. This rule governs what an
  implementation *emits* — receiving/consuming systems must instead treat an
  unrecognized enum value permissively, per `specification/conventions.md`; that
  permissive-consumption rule is not a runtime-validation rule for an emitting SDK and
  is out of scope for this document.
- **Source:** `specification/errors.md`, `specification/conventions.md` ("Enums").

### 2.4 Price/currency pairing violated
- **Applies to:** event
- **Trigger:** the event is one where a monetary amount and its currency are meant to
  travel together (currently `subscription_started` and `purchase_completed` in
  `events/*.yaml`, both of which declare optional, paired `price`/`currency`
  properties) and exactly one of the pair is present.
- **Required runtime behavior:** drop the unpaired property (never emit a bare `price`
  without `currency` or vice versa) and log a development diagnostic. This mirrors the
  metric envelope's identical currency-pairing rule (3.4) at the property level.
- **Source:** `specification/conventions.md` ("Numbers and currency" — "every monetary
  amount must be paired with a sibling currency property"), `events/monetization.yaml`.

### 2.5 Reserved property-key collision
- **Applies to:** event
- **Trigger:** a property key (canonical or app-specific) equals one of the envelope's
  reserved field names: `event`, `schema_version`, `timestamp`, `app_id`,
  `environment`, `platform`, `sdk_version`, `sdk_name`, `app_version`, `user_id`,
  `anonymous_id`, `properties`.
- **Required runtime behavior:** drop the colliding property and log a development
  diagnostic; never let an application-supplied property shadow or overwrite an
  envelope field.
- **Source:** `specification/conventions.md` ("Property keys must not collide with
  envelope field names").

### 2.6 Non-`snake_case` event name or property key
- **Applies to:** event
- **Trigger:** `event` or any property key does not match the `identifier` pattern
  (`^[a-z][a-z0-9_]*[a-z0-9]$`, minimum length 2) — for example camelCase, a leading
  digit, a leading/trailing underscore, or a non-lowercase character.
- **Required runtime behavior:** drop the offending event (if the name itself is
  invalid) or property (if only a key is invalid) and log a development diagnostic.
- **Source:** `specification/errors.md`, `specification/conventions.md`,
  `schema/common-types.yaml#/$defs/identifier`.

### 2.7 Unknown (non-canonical) event name
- **Applies to:** event
- **Trigger:** the event name does not match any entry in `events/*.yaml`.
- **Required runtime behavior:** **this is not malformed.** App-specific events are
  explicitly permitted. A conforming implementation should log a development-only
  diagnostic identifying the event as app-specific, purely as a visibility aid — it
  must not be dropped, corrected, or treated as an error for this reason alone. (It
  remains subject to every other rule in this document — casing, reserved-field
  collision, privacy — like any other event.)
- **Source:** `specification/errors.md` ("Unknown or custom event names").

### 2.8 `screen()` — missing screen name
- **Applies to:** event (the `screen_viewed` event specifically)
- **Trigger:** `screen()` is called with an empty or missing screen name.
- **Required runtime behavior:** drop the call and log a development diagnostic —
  `screen_name` is `screen_viewed`'s one required property (`events/application.yaml`).
- **Source:** `specification/screen-tracking.md`, `events/application.yaml`.

## 3. Metric-specific rules (`recordMetric`)

### 3.1 Missing required canonical dimension
- **Applies to:** metric
- **Trigger:** the metric name matches a canonical metric in `metrics/*.yaml`, and a
  dimension marked `required: true` on that metric's definition is absent from
  `dimensions`.
- **Required runtime behavior:** drop the offending metric and log a development
  diagnostic naming the missing dimension.
- **Source:** `specification/errors.md`, `schema/metric-dimensions.yaml`.

### 3.2 `value` missing, non-numeric, or negative
- **Applies to:** metric
- **Trigger:** `value` is absent, is not a number, or is negative.
  `schema/common-types.yaml#/$defs/metric_value` fixes `minimum: 0` — a metric value
  is always a non-negative magnitude; direction (e.g. a refund vs. a charge) is
  represented by a dimension, never by a negative `value`
  (`specification/metric-envelope.md`).
- **Required runtime behavior:** drop the metric and log a development diagnostic.
  Never coerce a negative value to its absolute value silently — that would silently
  change the metric's meaning; drop it instead.
- **Source:** `specification/errors.md`, `schema/common-types.yaml`.

### 3.3 `unit` missing or not an allowed value
- **Applies to:** metric
- **Trigger:** `unit` is absent or not one of `currency`, `count`, `impression`,
  `millisecond`, `second`, `other`.
- **Required runtime behavior:** drop the metric and log a development diagnostic. For
  a canonical metric, `unit` is fixed by the metric's own definition
  (`metrics/*.yaml`), so this should only occur from an adapter programming error, not
  application input.
- **Source:** `specification/errors.md`, `schema/common-types.yaml#/$defs/metric_unit`.

### 3.4 Currency pairing violated
- **Applies to:** metric
- **Trigger:** `unit` is `currency` and `currency` is absent, OR `unit` is not
  `currency` and `currency` is present.
- **Required runtime behavior:** if `unit` is `currency` and `currency` is missing,
  drop the metric (a currency amount without a currency code is meaningless and must
  not be emitted) and log a development diagnostic. If `currency` is present on a
  non-currency-unit metric, drop the stray `currency` field (correctable) and log a
  development diagnostic.
- **Source:** `specification/errors.md`, `specification/metric-envelope.md`,
  `schema/metric-envelope.yaml`.

### 3.5 Dimension value does not match its documented type
- **Applies to:** metric
- **Trigger:** a canonical dimension's supplied value does not match its declared type
  (`string`, `integer`, `boolean`, `enum` — a deliberately narrower set than event
  property types, per `schema/metric-dimensions.yaml`), or an `enum` dimension's value
  is not among its `allowed_values`.
- **Required runtime behavior:** correct if unambiguous, otherwise drop the dimension
  (or the metric, if the dimension was required, per 3.1) and log a development
  diagnostic.
- **Source:** `specification/errors.md`, `schema/metric-dimensions.yaml`.

### 3.6 Reserved dimension-key collision or non-`snake_case` key
- **Applies to:** metric
- **Trigger:** a dimension key collides with a reserved metric-envelope field name, or
  does not match the `identifier` pattern.
- **Required runtime behavior:** drop the offending dimension and log a development
  diagnostic — identical treatment to the event property equivalents (2.5, 2.6).
- **Source:** `specification/errors.md`, `specification/metric-envelope.md`.

### 3.7 `source` missing or not an allowed value
- **Applies to:** metric
- **Trigger:** `source` is absent or not one of `application`, `billing_system`,
  `advertising_system`, `operating_system`, `network`, `provider`, `other`.
- **Required runtime behavior:** drop the metric and log a development diagnostic.
- **Source:** `specification/errors.md`, `schema/common-types.yaml#/$defs/metric_source`.

### 3.8 Fixed-value metric emitted with a different value
- **Applies to:** metric
- **Trigger:** a canonical metric whose definition declares a `fixed_value` (currently
  `ad_impression` and `handled_error` in `metrics/*.yaml`, both fixed at `1`) is
  recorded with any other `value`.
- **Required runtime behavior:** correct the value to the metric's declared
  `fixed_value` and log a development diagnostic noting the correction, rather than
  dropping the metric. `errors.md`/`metrics.md`'s "correct what can be unambiguously
  corrected, or drop... or queue... in that order of preference" leaves room for
  either choice on any given rule; this is the one rule in this document where
  correction is chosen over dropping, because a `fixed_value` declaration makes the
  correct value genuinely unambiguous — there is exactly one possible right answer,
  not a heuristic guess. Contrast with 2.6's non-`snake_case` key, which drops instead:
  a case-style transliteration (e.g. `userName` → `user_name`) is a guess about
  intent, not a single unambiguously correct value, so dropping is the safer choice
  there even though it is superficially "fixable" too.
- **Source:** `metrics/*.yaml` (`fixed_value` declarations), `validation/validate.py`
  (already enforces the authoring-time version of this rule for example payloads).

### 3.9 `schema_version` missing or not a positive integer
- **Applies to:** metric (event covered by 1.2)
- **Trigger:** `schema_version` is absent or not a positive integer.
- **Required runtime behavior:** drop the metric and log a development diagnostic —
  same underlying rule as 1.1/1.2, restated because `specification/errors.md`
  states it explicitly for metrics.
- **Source:** `specification/errors.md`.

### 3.10 Unknown (non-canonical) metric name
- **Applies to:** metric
- **Trigger:** `metric_name` does not match any entry in `metrics/*.yaml`.
- **Required runtime behavior:** **this is not malformed**, identical treatment to
  2.7 — log a development-only diagnostic identifying it as app-specific; do not drop,
  correct, or error. Still subject to every other rule in this document.
- **Source:** `specification/errors.md` ("Unknown or custom metric names").

## 4. Identity rules

### 4.1 `identify()` called with an empty or missing `user_id`
- **Applies to:** identity (affects all subsequent events/metrics)
- **Trigger:** `identify()` is called with an empty string or no argument.
- **Required runtime behavior:** reject the call (no-op) and log a development
  diagnostic. Must not clear the currently active identity, must not emit an event
  with an empty `user_id`.
- **Source:** `specification/identity.md`.

### 4.2 `identify()` called with a different `user_id` while one is already active
- **Applies to:** identity
- **Trigger:** `identify(new_user_id)` is called where `new_user_id` differs from the
  currently active `user_id`, without an intervening `reset()`.
- **Required runtime behavior:** the contract explicitly leaves this undefined at the
  cross-app level ("not well-defined by this contract and must not be relied upon");
  an implementation must handle it defensively — never crash — and should log a
  development diagnostic flagging the misuse, but the specific defensive behavior
  (e.g. treat as a fresh identify, or ignore) is an adapter decision, not a contract
  rule this document can pin down further.
- **Source:** `specification/identity.md` ("Account switching semantics").

### 4.3 `reset()` must never reuse the previous `anonymous_id`
- **Applies to:** identity
- **Trigger:** N/A (this is a structural correctness requirement on `reset()` itself,
  not a malformed-input check) — included here because it is a runtime-observable
  invariant a conformance test suite must assert.
- **Required runtime behavior:** `reset()` must clear `user_id` and all
  `setUserProperties`-set properties, and must generate and persist a genuinely new
  `anonymous_id` distinct from the one it replaces.
- **Source:** `specification/identity.md`, `specification/privacy.md`.

## 5. Prohibited data (privacy) — runtime-checkable subset

`specification/privacy.md`'s prohibited-data list (passwords, auth/session tokens,
API keys, payment card data, private keys/secrets, unnecessary sensitive PII) is
largely not mechanically detectable at runtime by a generic SDK — a validator cannot
reliably distinguish a legitimate opaque string from a leaked secret by inspection
alone. This contract does not require (and no existing adapter implements) content
scanning of property/dimension values for prohibited data; compliance is achieved by
applications not passing such data in the first place, and by code review per
`privacy.md`'s exceptional-data process. The two things a runtime validator *can* and
must check mechanically are:

### 5.1 `reference_id` / `error_code` must not be used as free text
- **Applies to:** metric
- **Trigger:** not mechanically detectable in general; this is a documentation-level
  constraint on `reference_id` (opaque correlation handle only) and `handled_error`'s
  `error_code` dimension (stable category/code, never a raw exception message or
  stack trace fragment).
- **Required runtime behavior:** no mechanical check is prescribed; adapters should
  document this constraint for application developers (as this rule does) rather than
  attempt unreliable content sniffing.
- **Source:** `specification/privacy.md` ("reference_id opacity", "error_code
  opacity").

### 5.2 Dimension cardinality / type restriction is mechanically enforced
- **Applies to:** metric
- **Trigger:** covered already by 3.5 — a dimension's type is restricted to `string`,
  `integer`, `boolean`, `enum` (never a free-text-friendly `object`/`array`, unlike
  event properties). This restriction is itself the mechanical half of `privacy.md`'s
  "dimension cardinality" rule (bounding what a dimension can structurally carry);
  the "not free text" half is a documentation-level constraint like 5.1.
- **Source:** `specification/privacy.md` ("Dimension cardinality"),
  `schema/metric-dimensions.yaml`.

## 6. Reliability rules (govern how every rule above is enforced)

These are not additional payload checks — they are the non-negotiable rules
governing *how* a conforming implementation must apply every rule above.

- **R1 — Never crash.** No uncaught exception, unhandled promise rejection, or fatal
  error may originate from `initialize`, `track`, `identify`, `setUserProperties`,
  `screen`, `reset`, or `recordMetric`, under any input, for any rule above.
- **R2 — Never block.** None of the seven operations may synchronously block a
  user-facing action while applying these rules.
- **R3 — Order of preference.** When a rule above is violated: (1) correct if
  unambiguous, else (2) drop the offending event/metric/property/dimension and
  continue, else (3) queue for later resolution if the implementation supports that.
  The calling application must never observe an exception it must handle.
- **R4 — Provider isolation is separate from validation.** These rules govern what an
  adapter validates and emits *before* handing an envelope to a provider. A
  downstream provider's own failure (network error, rejection, timeout) is a distinct
  concern governed by `specification/errors.md` rule 4 ("provider failures must be
  isolated") — not a malformed-payload rule, and out of scope for this document.
- **R5 — Development diagnostics, production silence.** In `development`, violations
  of any rule above should be logged with enough detail to fix the bug (event/metric
  name, which rule, which field). In `production`, diagnostics for these violations
  must not leak raw property/dimension values, user identifiers beyond what's already
  in the envelope, or any `privacy.md`-prohibited category.
- **Source:** `specification/errors.md` (rules 1–6).

## Relationship to `validation/validate.py`

`validate.py` checks the **authoring-time** correctness of this repository's own
`events/*.yaml`, `metrics/*.yaml`, `schema/*.yaml`, and `examples/` files — it makes
sure the contract itself is internally consistent. This document and its companion
JSON file describe **runtime** checks a platform adapter's SDK code must perform on
values it receives from an application at call time. The two are complementary: many
rules here mirror a rule `validate.py` already enforces on the contract's own example
payloads (for example 3.8's fixed-value rule, or the currency-pairing rule 3.4), which
is expected — a rule true of the contract's own examples should also be true of every
payload emitted at runtime.
