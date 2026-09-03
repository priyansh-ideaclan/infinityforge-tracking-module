# Validation

`validate.py` runs lightweight, dependency-light consistency checks against this repository. It is not a full JSON Schema validator and is not wired into any CI system yet — it exists as a fast, local pre-review check.

## What it checks

- Every event definition in `events/*.yaml` has a unique, `snake_case` name
- Every event has `description`, `trigger`, `purpose`, `schema_version`, and `properties` documented
- Every property has a valid `type`, `required`/`common` booleans, and a description
- `enum`-typed properties have `allowed_values`; non-enum properties don't
- No property name collides with a reserved envelope field name
- Every metric definition in `metrics/*.yaml` has a unique, `snake_case` name
- Every metric has `description`, `trigger`, `purpose`, `schema_version`, `unit`, `typical_source`, `dimensions`, and `example` documented
- Every metric's `unit` and `typical_source` are among the documented allowed values, and its `example` path points to a file that exists
- Every declared metric `fixed_value` is a non-negative number, and each matching example uses that exact value
- Every dimension has a valid `type` (`string`/`integer`/`boolean`/`enum` only — a narrower set than event properties), a `required` boolean, and a description
- `enum`-typed dimensions have `allowed_values`; non-enum dimensions don't
- No dimension name collides with a reserved metric envelope field name
- Every file in `schema/*.yaml` is valid YAML
- Every example payload in `examples/payloads/*.json` is valid JSON, contains the required envelope fields, references a real event name, and uses only documented `environment`/`platform` values
- Every example payload in `examples/metrics/*.json` is valid JSON, contains the required metric envelope fields, references a real metric name, uses only documented `unit`/`source`/`environment`/`platform` values, has a non-negative `value`, and carries `currency` if and only if `unit` is `currency`
- No canonical event or metric is missing an example payload (warning, not an error)
- No forbidden vendor or framework term (Firebase, Amplitude, Mixpanel, PostHog, Segment, RudderStack, Crashlytics, Expo Router, React Navigation, SwiftUI, UIKit, Jetpack Compose, AdMob, RevenueCat, Google Analytics) appears anywhere in `specification/`, `events/`, `metrics/`, `schema/`, or `examples/` — `docs/` is intentionally exempt, since `docs/implementation-guide.md` is allowed to name real providers when discussing provider independence

## Running it

Requires [PyYAML](https://pypi.org/project/PyYAML/):

```
pip install pyyaml --break-system-packages
python3 validation/validate.py
```

Exit code is `0` when everything passes, non-zero otherwise.

## Runtime validation rules (validation/runtime/)

`validate.py` above validates this repository's own authoring-time files. It does not
describe what a platform adapter's SDK must check on values it receives from an
application at call time (`track`, `screen`, `identify`, `setUserProperties`,
`recordMetric`) — that is a distinct, language-neutral rule set derived from the same
specification files, kept in
[`validation/runtime/malformed-payload-rules.md`](runtime/malformed-payload-rules.md)
(prose, organized by rule) and
[`validation/runtime/malformed-payload-rules.json`](runtime/malformed-payload-rules.json)
(the same rules with stable ids, for an adapter's validator or test suite to reference
directly). Every rule there is a restatement of an existing rule in `specification/` or
`schema/` — see that document's own header for how the two relate.

## What it deliberately does not do

It does not validate against `schema/event-envelope.yaml` or `schema/event-properties.yaml` as formal JSON Schema documents (that would require a JSON Schema engine and a `$ref` resolver, which this Phase 1 repository intentionally leaves for later). It re-implements the same rules directly in Python instead, which is enough to catch the mistakes that actually tend to happen when hand-editing these files.
