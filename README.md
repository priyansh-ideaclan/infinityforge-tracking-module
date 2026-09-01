# InfinityForge Tracking Module

**The central, language-independent source of truth for how InfinityForge apps describe user behavior.**

This repository does not contain an analytics SDK. It contains the **Tracking Contract**: the conceptual specification that every InfinityForge platform implementation — React Native, Swift, Kotlin, and whatever comes next — must follow so that tracking data is meaningful, comparable, and compatible no matter which app template produced it.

---

## 1. What this repository is

`infinityforge-tracking-module` defines *what* InfinityForge tracking means, independent of any programming language, mobile framework, or analytics vendor. It specifies:

- the core tracking operations (`initialize`, `track`, `identify`, `setUserProperties`, `screen`, `reset`), plus the optional `recordMetric` operation for implementations that support the Metrics capability
- the canonical event envelope every event is wrapped in, and the metric envelope every metric is wrapped in
- the initial event taxonomy (application, authentication, onboarding, product, monetization)
- the metric taxonomy (monetization, advertising, engagement, performance, reliability) — raw measurements, distinct from both events and from derived/aggregated business metrics (see `specification/metrics.md`, `specification/derived-metrics.md`)
- identity rules (anonymous vs. authenticated state, login, logout, account switching)
- screen tracking semantics
- metadata ownership (who supplies which field, and when)
- privacy rules (what must never be tracked)
- error-handling rules (tracking must never break the app)
- versioning and compatibility rules

Both the human-readable specification (in `specification/`, `events/`, `docs/`) and a machine-readable schema (in `schema/`) live here, so the contract can be read by people and consumed by tooling.

## 2. What problem it solves

InfinityForge ships the same product concept across multiple app templates and technologies. Without a shared contract, each platform team would independently invent event names, property shapes, and identity rules — producing tracking data that cannot be joined, compared, or trusted across platforms. This repository exists so that a `subscription_started` event from the React Native template and a `subscription_started` event from the native Swift template describe the same thing, in the same shape, under the same identity rules.

## 3. Why it is language-independent

InfinityForge already has a React Native template and a native Swift/iOS template, and expects to add a Kotlin/Android template and, eventually, others (Flutter, web, Unity, or technologies not yet chosen). A contract written around any one of those — or around a specific analytics vendor's SDK — would not survive that growth. This repository is deliberately written so that:

- no framework, language, or navigation library is mentioned in the contract
- no analytics vendor (Firebase, Amplitude, Mixpanel, PostHog, Segment, RudderStack, or any other) is assumed, required, or referenced as part of the contract itself
- every rule is described in terms of *behavior and meaning*, not *syntax or implementation*

If InfinityForge changes analytics vendors, or adds a fifth app template in a language that doesn't exist yet, this contract should not need to change.

## 4. What belongs here

- Specification documents describing the tracking contract, identity model, screen tracking semantics, metadata ownership, privacy rules, error-handling rules, and versioning rules
- The canonical event taxonomy and event definitions (name, description, trigger, purpose, properties, examples)
- Machine-readable schema definitions for the event envelope and event properties
- Neutral, illustrative examples of conforming payloads
- Guidance for platform teams on how to implement the contract

## 5. What does NOT belong here

- Any platform-specific SDK or adapter code (React Native, Swift, Kotlin, or otherwise)
- Any analytics vendor integration (Firebase Analytics, Firebase Crashlytics, Amplitude, Mixpanel, PostHog, Segment, RudderStack, or any custom backend)
- A tracking backend, event ingestion API, or event database
- A dashboard or reporting tool
- Code generators
- API keys, credentials, certificates, or any other secret

Platform-specific implementations of this contract live in their respective app templates or in future dedicated SDK repositories — never in this repository.

## 6. How platform templates consume the contract

Each app template implements an **adapter (or SDK)** that exposes the six core operations defined in [`specification/api.md`](specification/api.md), emits events matching the envelope defined in [`schema/event-envelope.yaml`](schema/event-envelope.yaml), and follows the identity, privacy, error, and versioning rules defined in `specification/`. The adapter is free to choose its own internal implementation, its own analytics vendor(s), and its own idiomatic API surface for its language — as long as the conceptual contract and the resulting event data are preserved. An adapter may additionally support the optional Metrics capability — `recordMetric`, matching [`schema/metric-envelope.yaml`](schema/metric-envelope.yaml) — but is not required to; see [`specification/contract.md`](specification/contract.md)'s "Metric conformance" section.

```
InfinityForge Tracking Contract
            |
    +-------+-------+
    |       |       |
   RN     Swift    Kotlin
    |       |       |
    +-------+-------+
            |
       Compatible
        Tracking
```

See [`docs/implementation-guide.md`](docs/implementation-guide.md) for the full guidance platform teams should follow.

## 7. Current supported platforms

As of this writing, the following app templates exist or are planned within InfinityForge:

- **React Native app template** — currently the active implementation target for this contract
- **Native Swift/iOS app template** — already exists
- **Kotlin/Android app template** — may be added

This repository does not implement any of them. It only defines what each must conform to.

## 8. Future platform model

InfinityForge anticipates additional app templates over time — potentially including Flutter, web, Unity, or other technologies not yet chosen. Because this contract is language- and framework-independent, a future template implements the same contract the same way an existing template does: by building an adapter that satisfies `specification/` and `schema/`. No changes to this repository should be required merely because a new platform is added.

## 9. Versioning approach

This repository defines its own versioned contract, independent of any implementation's release cycle. See [`specification/versioning.md`](specification/versioning.md) for the full policy. In short:

- the **contract** has a semantic version (currently tracked in [`CHANGELOG.md`](CHANGELOG.md))
- each **event** and each **metric** carries its own integer `schema_version`
- additive, backward-compatible changes (e.g., a new optional property or a new optional dimension) do not require a major version bump
- changes that alter meaning, remove fields, or rename events are breaking and follow the deprecation process described in `specification/versioning.md`

## 10. How developers propose changes

See [`CONTRIBUTING.md`](CONTRIBUTING.md). In short: proposed changes to events, schema, or rules are made as pull requests against this repository, classified as compatible or breaking per `specification/versioning.md`, and reviewed before merge — especially any change that touches identity rules or introduces a new category of collected data, which requires explicit privacy review per `specification/privacy.md`.

---

## Repository structure

```
infinityforge-tracking-module/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
│
├── specification/          # Human-readable normative contract
│   ├── overview.md
│   ├── contract.md
│   ├── api.md
│   ├── conventions.md
│   ├── identity.md
│   ├── screen-tracking.md
│   ├── metadata.md
│   ├── privacy.md
│   ├── errors.md
│   ├── versioning.md
│   ├── events.md
│   ├── metrics.md            # Metric primitive, capability semantics, deduplication, sampling
│   ├── metric-envelope.md    # Metric envelope fields, value/unit/currency/source, dimensions
│   ├── metric-taxonomy.md    # Canonical metric list
│   └── derived-metrics.md    # Why derived business metrics are never emitted directly
│
├── events/                 # Canonical event taxonomy (machine-readable)
│   ├── application.yaml
│   ├── authentication.yaml
│   ├── onboarding.yaml
│   ├── product.yaml
│   └── monetization.yaml
│
├── metrics/                 # Canonical metric taxonomy (machine-readable)
│   ├── monetization.yaml
│   ├── advertising.yaml
│   ├── engagement.yaml
│   ├── performance.yaml
│   └── reliability.yaml
│
├── schema/                 # Machine-readable schema (JSON Schema-flavored YAML)
│   ├── common-types.yaml
│   ├── event-envelope.yaml
│   ├── event-properties.yaml
│   ├── metric-envelope.yaml
│   └── metric-dimensions.yaml
│
├── examples/
│   ├── events/              # Illustrative multi-call sequences
│   ├── payloads/             # One full example payload per canonical event
│   └── metrics/               # One full example payload per canonical metric
│
├── docs/
│   └── implementation-guide.md
│
└── validation/              # Lightweight, dependency-light consistency checks
    ├── validate.py
    └── README.md
```

## Start here

- New to this repository? Start with [`specification/overview.md`](specification/overview.md).
- Implementing a platform adapter? Start with [`specification/api.md`](specification/api.md) and [`docs/implementation-guide.md`](docs/implementation-guide.md).
- Adding or changing an event? Start with [`specification/events.md`](specification/events.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Adding or changing a metric? Start with [`specification/metrics.md`](specification/metrics.md), [`specification/metric-taxonomy.md`](specification/metric-taxonomy.md), and [`CONTRIBUTING.md`](CONTRIBUTING.md).
