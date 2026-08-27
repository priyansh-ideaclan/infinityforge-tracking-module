# Metadata Model

Every event carries a fixed set of metadata fields — the **event envelope**, defined machine-readably in `schema/event-envelope.yaml`. This document explains what each field means and, critically, **who supplies it**, so platform implementers know what they are responsible for populating versus what the SDK layer handles automatically.

## Field ownership

| Field | Supplied by | Notes |
|---|---|---|
| `event` | Application | The event name passed to `track`/`screen`, or the canonical name for `screen_viewed`. |
| `schema_version` | SDK | The `schema_version` of the event definition the SDK is emitting, per `events/*.yaml`. |
| `timestamp` | SDK | Captured automatically at the moment the operation is invoked. The application never supplies this. |
| `app_id` | Application | Configured once, typically at `initialize`. |
| `environment` | Application | Configured once, typically at `initialize`, from build configuration. See `versioning.md` and the Environment section below. |
| `platform` | SDK | Detected automatically at runtime from the operating system the app is running on. |
| `sdk_version` | SDK | The version of the adapter implementing this contract. |
| `sdk_name` | SDK | Identifies which conceptual adapter emitted the event (for example, distinguishing a React Native adapter from a native Swift adapter that may both run on the same `platform`). Optional — see rationale below. |
| `app_version` | Application (SDK may read it from platform package metadata) | The version or build identifier of the host application. |
| `user_id` | SDK, from identity state | Present only once `identify` has been called and not yet cleared by `reset`. See `identity.md`. |
| `anonymous_id` | SDK, from identity state | Always present. See `identity.md`. |
| `properties` | Application | Event-specific data passed to `track`/`screen`. |

No field is supplied directly by a backend at capture time. A backend or ingestion system may enrich data with additional fields downstream (for example, geo-location derived from an IP address), but that enrichment happens outside this contract and outside the emitted envelope — it is out of scope for this repository.

## Why `sdk_name` exists

InfinityForge intentionally supports multiple app templates that can target the same runtime platform — for example, both the React Native template and the native Swift template ultimately run as an iOS app, and would both report `platform: ios`. Without a separate field identifying which adapter produced the event, two structurally different implementations would be indistinguishable in the data during any period where multiple templates coexist or one is migrating to another. `sdk_name` is optional (not required) so that its absence never breaks conformance, but implementations should supply it whenever known.

## Environment

`environment` must be one of exactly three values:

- **`development`** — a build run by a developer on their own device or simulator/emulator during active development. Not distributed to any tester or user.
- **`preview`** — an internal or pre-release build distributed for testing, QA, or stakeholder review, but not available to the general public. This covers the role often called "staging" elsewhere in the industry; InfinityForge deliberately uses `preview` instead, and no third value should be introduced without a strong architectural reason recorded in `CONTRIBUTING.md`'s review process.
- **`production`** — a build available to real end users.

`environment` must accurately reflect the build's actual context. An implementation must never silently default to `production` when the true environment is unknown — an unknown environment is an implementation error to be surfaced in development, not defaulted away.

### Environment fallback

A platform's build tooling does not always have an explicit, per-build environment value configured for it to read. When no explicit value is configured, an implementation MAY fall back to a build-time signal that reliably distinguishes "this is a development build" from "this is not" (for example, a bundler's development-mode flag) — provided that signal is set by the build tooling itself, not by application code, and cannot be spoofed by ordinary configuration.

Such a fallback is an accepted exception to the rule above, under two conditions:

1. The signal is used only to decide between `development` and *not* `development` — it must never be used to decide between `preview` and `production`; a build-mode flag generally cannot tell those apart.
2. When the signal indicates "not development" and no explicit value was configured, the implementation defaults to `production` — the more restrictive, safer choice, since it suppresses development-only behavior rather than risking it in a real release build — and surfaces a lightweight diagnostic that this fallback occurred, through whatever diagnostic channel the implementation already has (specification/errors.md), rather than defaulting silently.

An implementation with no such reliable build-time signal available must treat an unconfigured environment as the implementation error described above. This fallback is a narrow, documented exception — not a general license to guess.

## No duplication

Each of these fields carries a single, non-overlapping purpose. Nothing here should be present in more than one place — for example, identity is only ever expressed through `user_id`/`anonymous_id`, never duplicated inside `properties`.
