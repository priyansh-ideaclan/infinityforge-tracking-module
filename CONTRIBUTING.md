# Contributing to the InfinityForge Tracking Module

This repository is the source of truth for the InfinityForge Tracking Contract. Because every platform template depends on it, changes here are reviewed more carefully than changes to a single application.

## Before you propose a change

Read:

1. [`specification/overview.md`](specification/overview.md) — the design principles this contract is built on
2. [`specification/versioning.md`](specification/versioning.md) — how to classify your change as compatible or breaking
3. [`specification/privacy.md`](specification/privacy.md) — if your change adds a new property or event, it must not collect prohibited data

## What kinds of changes are welcome

- New optional properties on an existing event (compatible change)
- New events that fit an existing category, or a clearly justified new category
- Clarifications to specification documents that resolve ambiguity without changing behavior
- New illustrative examples
- Improvements to the validation tooling

## What requires extra scrutiny

- Anything that changes the *meaning* of an existing field or event (breaking change — see `specification/versioning.md`)
- Anything that removes or renames an event or a required property (breaking change)
- Any new property or event intended to capture data that could be sensitive personal information — this requires explicit privacy review per `specification/privacy.md` before it is added, not after
- Any change to the identity model (`specification/identity.md`)
- Any change to the event envelope (`schema/event-envelope.yaml`)

## Checklist for adding a new event

1. Confirm the event doesn't already exist under a different name — check `events/*.yaml`.
2. Choose a category (`application`, `authentication`, `onboarding`, `product`, `monetization`, or propose a new one if none fit).
3. Name it in `snake_case` following [`specification/conventions.md`](specification/conventions.md).
4. Write `description`, `trigger`, and `purpose` in plain, implementation-neutral language — no mention of any specific framework, navigation library, or analytics vendor.
5. Define its properties: for each, a `name`, `type`, whether it is `required`, and a `description`. Only mark a property `required` if its semantics are unambiguous — see [`specification/events.md`](specification/events.md) for guidance on common vs. app-specific properties.
6. Set `schema_version: 1` for a brand-new event.
7. Add a corresponding example payload under `examples/payloads/`.
8. Run the validation script (`validation/validate.py`) before opening a pull request.

## Checklist for changing an existing event or the envelope

1. Classify the change using the compatibility table in `specification/versioning.md`.
2. If it is breaking, follow the deprecation process described there rather than editing the field in place.
3. Update the affected event's `schema_version` if, and only if, the change is a breaking change to that event's shape.
4. Update `CHANGELOG.md`.
5. Update any affected examples.

## Where things belong

| Content | Location |
|---|---|
| Normative rules and semantics | `specification/` |
| Canonical event definitions | `events/` |
| Machine-readable envelope/property schema | `schema/` |
| Illustrative payloads | `examples/` |
| Guidance for platform implementers | `docs/` |

Platform-specific implementation code never belongs in this repository, regardless of how small. It belongs in the relevant app template or a future dedicated SDK repository.

## Review

Pull requests are reviewed for:

- language-independence (no vendor or framework references leaking into `specification/`, `events/`, or `schema/`)
- consistency with existing terminology (see `specification/conventions.md`)
- correct compatible/breaking classification
- privacy compliance for any new data collection

Use `validation/validate.py` to catch structural and terminology issues before requesting review.
