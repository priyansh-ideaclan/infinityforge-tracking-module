# Validation

`validate.py` runs lightweight, dependency-light consistency checks against this repository. It is not a full JSON Schema validator and is not wired into any CI system yet — it exists as a fast, local pre-review check.

## What it checks

- Every event definition in `events/*.yaml` has a unique, `snake_case` name
- Every event has `description`, `trigger`, `purpose`, `schema_version`, and `properties` documented
- Every property has a valid `type`, `required`/`common` booleans, and a description
- `enum`-typed properties have `allowed_values`; non-enum properties don't
- No property name collides with a reserved envelope field name
- Every file in `schema/*.yaml` is valid YAML
- Every example payload in `examples/payloads/*.json` is valid JSON, contains the required envelope fields, references a real event name, and uses only documented `environment`/`platform` values
- No canonical event is missing an example payload (warning, not an error)
- No forbidden vendor or framework term (Firebase, Amplitude, Mixpanel, PostHog, Segment, RudderStack, Crashlytics, Expo Router, React Navigation, SwiftUI, UIKit, Jetpack Compose) appears anywhere in `specification/`, `events/`, or `schema/` — `docs/` is intentionally exempt, since `docs/implementation-guide.md` is allowed to name real providers when discussing provider independence

## Running it

Requires [PyYAML](https://pypi.org/project/PyYAML/):

```
pip install pyyaml --break-system-packages
python3 validation/validate.py
```

Exit code is `0` when everything passes, non-zero otherwise.

## What it deliberately does not do

It does not validate against `schema/event-envelope.yaml` or `schema/event-properties.yaml` as formal JSON Schema documents (that would require a JSON Schema engine and a `$ref` resolver, which this Phase 1 repository intentionally leaves for later). It re-implements the same rules directly in Python instead, which is enough to catch the mistakes that actually tend to happen when hand-editing these files.
