# Event Taxonomy

This document explains how the canonical event catalog is organized and how each event is documented. The event definitions themselves are machine-readable YAML files under `events/`, one file per category.

## Categories

| Category | File | Events |
|---|---|---|
| Application | `events/application.yaml` | `app_opened`, `screen_viewed` |
| Authentication | `events/authentication.yaml` | `signup_started`, `signup_completed`, `login_started`, `login_completed` |
| Onboarding | `events/onboarding.yaml` | `onboarding_started`, `onboarding_completed` |
| Product | `events/product.yaml` | `feature_used` |
| Monetization | `events/monetization.yaml` | `paywall_viewed`, `trial_started`, `subscription_started`, `subscription_cancelled`, `purchase_completed` |

This is the **initial** taxonomy. New events are added through the process in `CONTRIBUTING.md`, following the compatibility rules in `versioning.md`.

## How an event is documented

Every entry in `events/*.yaml` includes:

| Field | Meaning |
|---|---|
| `name` | The canonical event name, `snake_case` |
| `description` | What the event represents |
| `trigger` | The condition under which it should be emitted |
| `purpose` | Why this event exists — what question it lets someone answer |
| `schema_version` | This event's own schema version (see `versioning.md`) |
| `properties` | The list of documented properties (see below) |
| `example` | A path to a full example payload under `examples/payloads/` |

Each entry in `properties` follows the shape defined in `schema/event-properties.yaml`: `name`, `type`, `required`, `description`, and — for `type: enum` — `allowed_values`.

## Common properties vs. app-specific properties

Every property listed inside `events/*.yaml` is a **common property**: part of the contract, with an agreed meaning across every InfinityForge app and platform. These are marked `common: true` in their definition.

Applications may additionally send **app-specific properties** on any event — properties not listed in the event's definition at all. This contract does not forbid that. App-specific properties:

- must still follow the naming and typing conventions in `conventions.md`
- must still comply with `privacy.md`
- must not reuse a common property's name with a different meaning
- carry no cross-app or cross-platform compatibility guarantee — they are meaningful only within the application that defines them

This separation is intentional: it keeps the canonical contract small and precisely defined, while still letting individual apps track what matters to them without waiting for a change to this repository. See `versioning.md`'s "App-specific event schema_version" section for how such an event's `schema_version` is assigned — it is not centrally defined here either.

## Required properties are conservative by design

Per `CONTRIBUTING.md`, a property is only marked `required` on a canonical event when its semantics are unambiguous and clearly necessary for the event to be meaningful (for example, `screen_name` on `screen_viewed`). Where a property is commonly useful but not strictly necessary to the event's meaning, it is documented as optional rather than required, so that implementations are not forced to invent values they don't actually have.
