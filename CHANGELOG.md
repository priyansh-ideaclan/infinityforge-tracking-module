# Changelog

All notable changes to the InfinityForge Tracking Contract are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [`specification/versioning.md`](specification/versioning.md).

## [Unreleased]

_No unreleased changes yet._

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
