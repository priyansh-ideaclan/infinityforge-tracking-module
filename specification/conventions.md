# Naming, Casing, and Type Conventions

These conventions apply to every event name and property key emitted on the wire — canonical or app-specific. They exist so that data from every platform implementation is uniform, regardless of the idiomatic casing conventions of the language that produced it.

## Naming and casing

**`snake_case` is used for every event name, property key, and enum value in the emitted contract.** This is a deliberate, explicit decision: it is the one convention consistently readable across YAML, JSON, and every backend and analytics system this data may eventually reach, and it avoids ambiguity between platforms whose idiomatic in-language casing differs (`camelCase` in TypeScript/Swift/Kotlin call sites vs. wire format).

A platform adapter may use whatever casing is idiomatic for its own language internally, but **must convert to `snake_case` before an event crosses the wire.** The contract only governs the emitted shape, not in-code identifiers.

**Event names** follow a `{subject}_{action}` pattern, generally with the action in past tense for an occurrence that has completed (for example `signup_completed`, `screen_viewed`) or present/started tense for the beginning of a flow (`signup_started`). New events should follow the pattern already established in `events/*.yaml` rather than introducing a new pattern.

**Property keys** must not collide with envelope field names. The following names are reserved by the envelope (`schema/event-envelope.yaml`) and must not be reused as property keys: `event`, `schema_version`, `timestamp`, `app_id`, `environment`, `platform`, `sdk_version`, `sdk_name`, `app_version`, `user_id`, `anonymous_id`, `properties`.

## Primitive types

The contract recognizes the following property types:

| Type | Description |
|---|---|
| `string` | Free text or a stable identifier |
| `integer` | A whole number |
| `number` | A decimal number |
| `boolean` | `true` or `false` only |
| `timestamp` | An ISO 8601 UTC string, see below |
| `enum` | A string drawn from a documented, closed set of allowed values |
| `object` | A nested key-value structure, itself following these conventions recursively |
| `array` | A homogeneous list of one of the above types |

## Objects and arrays

Use `object` and `array` sparingly. A property should be a flat primitive wherever possible. Nested objects are acceptable when a value genuinely has internal structure (for example, a range or a compound identifier); deeply nested arrays of objects should be avoided in event properties — if a payload needs that level of structure, reconsider whether it should be multiple simpler events instead.

## Booleans

Only the literal values `true` and `false` are valid. Do not represent booleans as the strings `"true"`/`"false"`, or as `0`/`1`.

## Numbers and currency

A monetary amount is expressed as a decimal `number` in the currency's **major unit** (for example, `4.99` for $4.99 — never minor units like cents, and never a currency symbol embedded in the value). Every monetary amount must be paired with a sibling `currency` property: a `string` holding an uppercase three-letter ISO 4217 currency code (for example `"USD"`, `"INR"`).

## Timestamps

Timestamps are ISO 8601 strings in UTC, including the `Z` designator (for example `2026-01-01T12:00:00Z`). The envelope's `timestamp` field is captured at the moment the operation is invoked — see `metadata.md`.

## Enums

Enum values are lowercase `snake_case` strings drawn from a closed, documented set specific to the property. New allowed values may be added to an enum over time as a compatible change (`versioning.md`); consuming systems must treat an unrecognized enum value permissively (log it, don't fail on it) rather than assuming the set is exhaustive forever.

## Null and absent values

**Omit optional properties rather than sending `null`** when a value does not apply. If an implementation's language forces an explicit null/optional representation internally, that representation must be resolved (either populated or stripped) before the event is emitted — `null` must never appear in an emitted event, and a required field must never be missing or null.

## Summary

| Rule | Value |
|---|---|
| Event/property/enum casing | `snake_case` |
| Boolean representation | `true` / `false` literals only |
| Currency amount | decimal, major unit, paired with `currency` (ISO 4217) |
| Timestamp format | ISO 8601, UTC, `Z` suffix |
| Absent values | omit the key — never emit `null` |
