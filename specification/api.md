# Core Operations

This document specifies the six core operations of the Tracking Contract, plus the optional `recordMetric` operation added for implementations that support the Metrics capability (`specification/metrics.md`, `contract.md`'s "Metric conformance" section). Each is described in terms of purpose, inputs, and behavior — never in terms of implementation syntax.

> Convention used below: "application" means the app code calling the operation; "SDK" means the platform adapter implementing this contract.

---

## initialize

**Purpose.** Prepares the tracking system for use: establishes configuration and ensures an identity exists before any other operation is meaningful.

**Inputs.** `app_id`, `environment`, and any implementation-defined configuration (for example, a diagnostics/verbose mode).

**Required fields.** `app_id`, `environment`.

**Optional fields.** Implementation-defined configuration. This contract does not define what configuration `initialize` accepts beyond the two required fields.

**Expected behavior.** Must be safe to call before any other operation is used. If an implementation loads a previously persisted identity (see `identity.md`), `initialize` is where that happens; if none exists, a new `anonymous_id` is established here. Calling `initialize` more than once must not create a second identity or duplicate configuration — a repeat call is either a no-op or safely reconciles configuration.

**Identity implications.** Establishes the initial `anonymous_id` if none is currently persisted for this install.

**Failure behavior.** Must never throw an uncaught error or crash the host app. If initialization cannot complete (for example, persisted state is unreadable), the implementation should fall back to a fresh anonymous identity and continue, surfacing a diagnostic only in development (see `errors.md`).

**Privacy considerations.** `app_id` and any configuration values must not themselves encode personal information.

---

## track

**Purpose.** Records that a named event occurred, optionally carrying event-specific properties.

**Inputs.** An event name, and an optional properties object.

**Required fields.** The event name. It must be a documented canonical event name (`events/*.yaml`) or an app-specific event name following `conventions.md`.

**Optional fields.** The properties object. Individual events may mark specific properties as required — see the event's own definition.

**Expected behavior.** Emits exactly one event envelope per call (`schema/event-envelope.yaml`), stamped with the identity, metadata, and timestamp current at the moment of the call. `track` is conceptually fire-and-forget from the calling application's perspective — it does not return event data to the application, and the application does not need to wait for it to complete.

**Identity implications.** None — `track` does not change identity state. The emitted event is associated with whichever identity is currently active (`user_id` if identified, otherwise `anonymous_id`).

**Failure behavior.** An unrecognized property type, a missing required property, or a malformed event name must be handled per `errors.md` — never as an uncaught exception in the calling application.

**Privacy considerations.** Properties must not contain any of the prohibited data categories in `privacy.md`.

---

## identify

**Purpose.** Binds the current session to a known `user_id`, establishing (or reaffirming) the authenticated identity state.

**Inputs.** A `user_id`.

**Required fields.** `user_id`. This contract's minimal model treats identity binding and user property assignment as separate concerns — user-level attributes are set via `setUserProperties`, not bundled into `identify`. An implementation may offer a convenience form that accepts both, but the conceptual operation defined by this contract is identity binding alone.

**Optional fields.** None at the contract level.

**Expected behavior.** Sets the active `user_id` for the session. Events recorded after `identify` include this `user_id` alongside the existing `anonymous_id`, linking the two for downstream identity resolution. Calling `identify` again with the *same* `user_id` reaffirms it and has no additional effect. Calling `identify` with a *different* `user_id` than the one currently active, without an intervening `reset`, is an account switch performed incorrectly — see `identity.md` for required behavior and why applications must call `reset` before `identify` when switching between two known accounts.

**Identity implications.** This is the operation that transitions a session from anonymous to authenticated. See `identity.md` for the full lifecycle.

**Failure behavior.** A missing or empty `user_id` must be rejected as a no-op — it must never silently clear the current identity. This must never crash the host app.

**Privacy considerations.** `user_id` must be an opaque, application-controlled identifier. It must not itself be an email address, phone number, or other raw personal identifier.

---

## setUserProperties

**Purpose.** Attaches or updates descriptive, persistent attributes about the current identity (anonymous or authenticated), as opposed to `track`, which records a discrete occurrence.

**Inputs.** A properties object.

**Required fields.** At least one property; an empty call is a no-op.

**Optional fields.** Not applicable — all properties are, by nature, optional to the caller.

**Expected behavior.** Merges the given keys onto the current identity's persistent property set. These properties persist across app sessions and across subsequent events until explicitly changed or cleared by `reset`. `setUserProperties` does not itself emit a discrete named business event.

**Identity implications.** Applies to whichever identity is currently active. If called before `identify`, the properties are associated with the current `anonymous_id`; how (or whether) they carry forward once the session is later identified is a backend/downstream concern outside this contract's scope.

**Failure behavior.** Invalid values are handled per `errors.md` — never as an uncaught exception.

**Privacy considerations.** The same prohibited categories from `privacy.md` apply here, with extra caution warranted because these properties are persistent rather than a single-event occurrence.

---

## screen

**Purpose.** Records that the user is now viewing a given screen. Conceptually a specialized form of `track` that emits the canonical `screen_viewed` event — see `screen-tracking.md` for the full semantic definition of a "screen."

**Inputs.** A `screen_name`, and an optional properties object.

**Required fields.** `screen_name`.

**Optional fields.** The properties object, per `screen-tracking.md`.

**Expected behavior.** See `screen-tracking.md`, including the duplicate-event policy.

**Identity implications.** None — stamped with whichever identity is currently active, exactly like `track`.

**Failure behavior.** A missing or empty `screen_name` must be rejected as a no-op, handled per `errors.md`.

**Privacy considerations.** `screen_name` must be a stable, logical identifier chosen by the application (for example, a route or view identifier) — never a dynamic value containing personal information.

---

## reset

**Purpose.** Clears the current identity and all user-level state, establishing a fresh anonymous identity. Used on logout or when switching between authenticated accounts.

**Inputs.** None.

**Required fields.** Not applicable.

**Optional fields.** Not applicable.

**Expected behavior.** Clears the current `user_id` and any properties set via `setUserProperties`, and establishes a new `anonymous_id`. The previous identity must not be silently reused or implicitly carried into subsequent events. See `identity.md` for the full lifecycle, including account-switching guidance.

**Identity implications.** Central to the identity model — see `identity.md`.

**Failure behavior.** Must never crash the host app. If persisted state cannot be fully cleared, the implementation must still stop associating *subsequent* events with the old identity, and should surface a diagnostic in development.

**Privacy considerations.** `reset` exists specifically to protect users on shared or reused devices. An implementation must not allow the previous `user_id` to reappear in event traffic once `reset` has completed.

---

## recordMetric (optional — Metrics capability)

**Purpose.** Records a raw, measured value at a point in time — the Metric counterpart to `track`. See `specification/metrics.md` for the full semantic model of when to use a Metric instead of (or alongside) an Event.

**Capability status.** Unlike the six operations above, `recordMetric` is not required for base conformance to this contract (`contract.md`'s "The six operations" / "Conformance requirements"). It is part of an optional, additive capability layer: an implementation may conform fully to this contract while exposing only the six core operations and never calling `recordMetric`. An implementation that emits any metric at all, however, must implement `recordMetric` exactly as specified here — see `contract.md`'s "Metric conformance (optional capability)" section for the precise conformance rule.

**Inputs.** A `metric_name`, a `value`, a `unit`, a `source`, and an optional `currency`, `reference_id`, and `dimensions` object.

**Required fields.** `metric_name` — a documented canonical metric name (`metrics/*.yaml`) or an app-specific metric name following `conventions.md`. `value` — a non-negative number. `unit` — fixed per `metric_name` by that metric's definition; the caller supplies it, but it must match the metric's documented `unit`. `source`. Any dimension the metric's own definition marks `required: true`.

**Optional fields.** `currency` (required only when `unit` is `currency`, forbidden otherwise), `reference_id`, and any optional `dimensions` the metric's definition documents. Individual metrics may mark specific dimensions as required — see the metric's own definition, exactly as `track` defers to an event's own definition for its properties.

**Expected behavior.** Emits exactly one metric envelope per call (`schema/metric-envelope.yaml`), stamped with the identity, metadata, and timestamp current at the moment of the call — the identical stamping rule `track` uses. `recordMetric` is conceptually fire-and-forget from the calling application's perspective, exactly like `track`: it does not return data to the application, and the application does not need to wait for it to complete.

**Identity implications.** None — `recordMetric` does not change identity state. The emitted metric is associated with whichever identity is currently active (`user_id` if identified, otherwise `anonymous_id`), exactly like `track`.

**Failure behavior.** A malformed metric (`specification/metrics.md` section 9, `errors.md`'s metrics subsection) must be handled per those same non-negotiable error-handling rules that govern the six core operations: never an uncaught exception, never a blocked user-facing action, corrected/dropped/queued in that order of preference.

**Privacy considerations.** `dimensions` must not contain any of the prohibited data categories in `privacy.md`, including that document's metrics-specific subsection.
