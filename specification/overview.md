# Overview

## What this contract is

The InfinityForge Tracking Contract defines, independent of any programming language or platform, what it means for an InfinityForge app to "track" user behavior. It specifies a small set of conceptual operations, a canonical event structure, a fixed initial vocabulary of events, and the rules of behavior (identity, privacy, error handling, versioning) that every platform implementation must follow.

It does not specify how any of this is implemented. There is no method signature, no class name, no import statement anywhere in this specification. A team implementing this contract in React Native, Swift, Kotlin, or a technology that doesn't exist yet should be able to read this repository and build a conforming adapter without needing to look at any other platform's code.

## Where this fits

```
                         INFINITYFORGE
                              |
                              v
             infinityforge-tracking-module
                       SOURCE OF TRUTH
                              |
                    Tracking Contract
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
       React Native         Swift            Kotlin
        Adapter/SDK       Adapter/SDK       Adapter/SDK
             |                |                |
             v                v                v
        RN Template       iOS Template    Android Template
```

This repository sits above every platform template. Platform teams build an adapter (an SDK) that implements this contract, and that adapter is what an app template actually depends on. This repository never depends on a template, and a template never defines part of this contract by itself.

## Design principles

**Platform neutrality.** Nothing in `specification/`, `events/`, or `schema/` may reference a specific programming language, UI framework, navigation library, or analytics vendor. If a rule can only be expressed by naming a specific technology, it does not belong in this contract — it belongs in a platform adapter's own documentation.

**Behavioral compatibility over implementation uniformity.** Two adapters do not need to share code, architecture, or internal design. They need to produce event data that is structurally and semantically compatible, so that data from a React Native app and a Swift app can be joined and compared meaningfully.

**Fail-safe by default.** Tracking is not core application functionality. Every rule in this contract is written so that a correct implementation can never crash the host app or block a user-facing action because of a tracking failure. See `specification/errors.md`.

**Privacy by default.** This contract defines categories of data that must never be tracked, and requires explicit review before any exceptional sensitive data is collected. See `specification/privacy.md`.

**Precision over convenience.** Every field, every event, and every rule in this contract exists because its meaning is clear and its purpose is documented. Fields are not added merely because other analytics platforms commonly have them.

**Extensibility without breakage.** The contract is expected to grow — new events, new optional properties, new app templates. `specification/versioning.md` defines how growth happens without breaking existing implementations or existing data.

## What this contract does not do

This is a Phase 1, specification-only repository. It deliberately does not include:

- an implementation of any platform SDK (React Native, Swift, Kotlin, or otherwise)
- an integration with any specific analytics vendor — this contract names no vendor anywhere; see docs/implementation-guide.md for how provider independence is preserved
- a tracking backend, event ingestion API, or event database
- a dashboard or reporting tool
- code generators

Those are all legitimate future work, but they build *on top of* this contract in separate repositories, once this contract exists.

## How to read this repository

| If you want to... | Start with... |
|---|---|
| Understand the contract's shape and guarantees | `specification/contract.md` |
| Implement or call the six core operations | `specification/api.md` |
| Understand naming, casing, and type conventions | `specification/conventions.md` |
| Understand anonymous/authenticated identity | `specification/identity.md` |
| Understand what a "screen" is and when to report one | `specification/screen-tracking.md` |
| Understand who supplies each envelope field | `specification/metadata.md` |
| Understand what must never be tracked | `specification/privacy.md` |
| Understand how tracking failures must be handled | `specification/errors.md` |
| Understand how the contract evolves over time | `specification/versioning.md` |
| Understand the event taxonomy and how events are documented | `specification/events.md` |
| See the canonical event definitions | `events/*.yaml` |
| See the machine-readable envelope and property schema | `schema/*.yaml` |
| See what conforming data looks like | `examples/` |
| Implement a new platform adapter | `docs/implementation-guide.md` |
