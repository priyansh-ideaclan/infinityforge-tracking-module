# Changelog

All notable changes to the InfinityForge Tracking Contract are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [`specification/versioning.md`](specification/versioning.md).

## [Unreleased]

_No unreleased changes yet._

## [1.1.0] - 2026-08-26

### Added

- `specification/versioning.md`: an explicit "App-specific event schema_version" rule — what it means, who assigns it (the application, never this contract or a platform adapter), that it starts at `1`, when it increments, what counts as a breaking vs. compatible change to it, that different applications version their own app-specific events independently, and that it is always an envelope field, never a separate central definition. Closes a gap platform implementers had previously been left to assume on their own.
- `specification/metadata.md`: an "Environment fallback" subsection documenting the narrow, accepted exception under which an implementation may resolve `environment` from a build-time development/not-development signal instead of an explicit configured value, without violating the "never silently default to production when unknown" rule — conditioned on the signal only ever distinguishing `development` from *not* `development`, defaulting to `production` (not `preview`) in the fallback case, and surfacing a diagnostic when it fires.
- `specification/events.md`: cross-reference to the new app-specific `schema_version` rule.

## [1.0.0] - 2026-08-26

### Added

- Initial publication of the InfinityForge Tracking Contract.
- Core tracking operations: `initialize`, `track`, `identify`, `setUserProperties`, `screen`, `reset` (`specification/api.md`).
- Canonical event envelope and metadata ownership model (`schema/event-envelope.yaml`, `specification/metadata.md`).
- Identity model covering anonymous/authenticated state, login, logout, and account switching (`specification/identity.md`).
- Screen tracking semantics (`specification/screen-tracking.md`).
- Privacy rules and prohibited data categories (`specification/privacy.md`).
- Error-handling rules (`specification/errors.md`).
- Versioning and compatibility rules (`specification/versioning.md`).
- Property and naming conventions (`specification/conventions.md`).
- Initial event taxonomy across five categories — application, authentication, onboarding, product, monetization — totaling 14 canonical events (`events/`).
- Machine-readable schema for the envelope and event property definitions (`schema/`).
- Illustrative example payloads for every canonical event (`examples/`).
- Platform implementation guidance (`docs/implementation-guide.md`).
- Lightweight, dependency-light validation tooling (`validation/`).
