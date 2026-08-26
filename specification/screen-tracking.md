# Screen Tracking Semantics

This document defines what a "screen" means in InfinityForge tracking, and when `screen_viewed` should be recorded. It intentionally says nothing about how navigation is implemented or detected — no router, no navigation library, and no UI framework is referenced anywhere in this document. That is a platform adapter's concern, not the contract's.

## What a screen is

A **screen** is a distinct, user-perceivable unit of navigable content or context — the "place" the user currently understands themselves to be in the app. It is defined by user perception, not by any particular technical construct: it does not matter whether that place is implemented as a full-screen route, a tab, a step in a flow, or something else — what matters is whether, from the user's point of view, they have moved somewhere new.

## When screen_viewed should be emitted

`screen_viewed` should be emitted when the user's active screen context changes to a new distinct screen. It should **not** be emitted for every visual re-render or minor state change within the same screen. Whether a transient overlay or modal constitutes a distinct screen is an application decision — but that decision should be applied consistently within a given app, so that the resulting data is comparable across sessions.

## Required screen name

`screen_name` is required on every `screen_viewed` event. It must be a **stable, logical identifier** chosen by the application — for example, a route, view, or step identifier — following the naming conventions in `conventions.md`. It must never be, or contain, a dynamic value that could carry personal information (a person's name, a search query, free text, or similar). Use a stable category or identifier instead of the dynamic content itself.

## Optional properties

Implementations may include a `previous_screen` property identifying the screen the user was on immediately prior, when that is known and meaningful. Applications may add further app-specific properties describing the screen context, following `conventions.md` and `privacy.md`.

## Duplicate event policy

A conforming implementation should not emit two consecutive `screen_viewed` events for the same `screen_name` without an intervening change of screen context. Re-renders, minor state updates, or repeated calls describing the same, still-current screen should be suppressed rather than recorded again. Genuinely leaving a screen and later returning to it (a new navigation into a screen the user was previously on) is a new occurrence and should be recorded again.

## Nested and repeated navigation

This contract does not define stack-based, tab-based, or any other specific navigation topology. Each time the user's active screen context changes to a distinct screen — including returning to a screen previously left — that is one `screen_viewed` occurrence, evaluated under the duplicate policy above. How an application structures its navigation internally does not change this semantic.
