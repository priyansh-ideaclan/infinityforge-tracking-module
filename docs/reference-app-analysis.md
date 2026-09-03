# Reference App vs. InfinityForge Tracking Module — Architecture Analysis

**Scope:** `Messages-Home-Source-v1.0` (reference app) vs. `infinityforge-tracking-module` (contract repo)
**Date:** 2026-09-03
**Author:** Analysis produced with Claude, for Razat / Ideaclan

---

## 0. Headline finding (read this first)

The prompt that kicked off this analysis assumed the reference app is a **React Native / Expo** app. It is not. `Messages-Home-Source-v1.0` is a **native Android application written in Java** — package `com.hdcamera.beauty`, Gradle 8.13.2, minSdk 24 / targetSdk 36, Java 17. It has no `package.json`, no JS/TS anywhere, no Expo, no React Navigation. It is a phone-launcher / home-screen app bundled with a beauty-camera module, monetized entirely through Google Mobile Ads (AdMob + Ad Manager), with Firebase Analytics and Crashlytics for telemetry. There is no login, no accounts, no subscriptions, and no in-app purchases anywhere in the codebase.

This matters because it changes what "the reference app" can teach us. It cannot show us an RN/Expo tracking pattern — there isn't one to find. What it *can* show us, in very high production-quality code, is:

1. How a real InfinityForge-adjacent app actually calls Firebase Analytics today (directly, with no abstraction layer beyond one thin static class).
2. How a real app builds a resilient network layer for something it fetches remotely (a remote ad-config document) — retries, backoff, ETag caching, stale-while-revalidate, fail-closed behavior. This is the single most reusable architectural pattern in the whole repo, and it has nothing to do with analytics.
3. How ad revenue/impression telemetry is normalized before being sent to Firebase — which turns out to be an almost exact real-world instance of what `infinityforge-tracking-module`'s **Metrics capability** (`ad_impression`, `ad_revenue`) was designed for.
4. What a "cross-platform tracking foundation" is up against on the native side: no shared envelope, no schema, no identity model beyond what Firebase manages invisibly, and one single hard-coded provider.

The second headline finding is about `infinityforge-tracking-module` itself: **it is not an SDK, and was never meant to be one.** Its own README states this in the first paragraph: *"This repository does not contain an analytics SDK. It contains the Tracking Contract."* There is zero executable code in it beyond a 416-line Python script (`validation/validate.py`) that lints the *specification files themselves* (naming, required docs fields, forbidden vendor terms) — it does not validate a single runtime event payload. Every other file is Markdown or YAML: specification prose, canonical event/metric definitions, JSON Schema-flavored type definitions, and illustrative example payloads.

So this is not really a comparison of two implementations. It is a comparison of **one full production implementation of an ad-hoc, un-versioned, single-vendor tracking approach** against **one carefully written, disciplined, but entirely unimplemented specification.** That reframing drives most of the recommendations in this report.

---

## A. Reference app architecture

### A.1 Tech stack

| Layer | What it actually is |
|---|---|
| Language / runtime | Java 17, native Android (no Kotlin, no JS) |
| Build system | Gradle 8.13.2, Android Gradle Plugin, `com.google.gms.google-services`, `com.google.firebase.crashlytics` plugins |
| Min/target SDK | minSdk 24, targetSdk 36, compileSdk 36 |
| UI | Classic Android `Activity` + `ViewBinding`, no Compose, no Fragment-heavy architecture |
| Camera | CameraX (`camera-core`, `camera-camera2`, `camera-lifecycle`, `camera-view`, `camera-extensions`) — deliberately uses the OEM's native HDR/Night/Portrait/Face-Retouch pipelines rather than a third-party beauty SDK |
| Ads | `com.google.android.gms:play-services-ads` (AdMob/Ad Manager), Google UMP (`user-messaging-platform`) for consent |
| Attribution | `com.android.installreferrer` (Play Install Referrer API) |
| Analytics | `com.google.firebase:firebase-analytics` (via Firebase BoM 34.17.0) |
| Crash reporting | `com.google.firebase:firebase-crashlytics` — gradle-plugin-driven automatic crash capture only |
| No RN/Expo, no navigation library, no Redux/MobX/ViewModel-based state layer, no networking library (Retrofit/OkHttp) — the one HTTP call in the app uses raw `HttpURLConnection` | |

### A.2 Application shape

This is a **home-screen launcher app** (`AndroidManifest.xml` declares `.act.LaunchHomeComActivity` with `category.HOME`), bundled with a beauty-camera/photo-editor module, a "cleaner"/cache-cleaning report screen, and a charging-status screen. It is not a typical "screens + business logic" mobile app — it behaves more like a system surface (home screen replacement) that happens to embed a camera product.

Package layout (`launcher/src/main/java/com/hdcamera/beauty/`):

- `act/` — ~20 `Activity` subclasses (`BeautyStudioComActivity`, `BeautyCameraComActivity`, `PhotoEditorComActivity`, `VideoStudioComActivity`, `LaunchHomeComActivity`, `SplashComActivity`, `ChargingStatusComActivity`, `CleanerReportComActivity`, …)
- `ads/` — the largest package (~25 files): the entire ad-serving, ad-health, ad-config, and ad-telemetry subsystem
- `other/` — home-screen mechanics, `BaseComActivity`, locale handling, `SharedPreferences`-backed stores
- `analytics/` — exactly one file, `BeautyAnalytics.java`
- `model/`, `receiver/` — small support classes
- `LauncherApplication.java` — the `Application` subclass and composition root

### A.3 Navigation

There is no navigation library. Screens are plain `Activity`s launched via `Intent`, wired together directly in each Activity's click handlers. `BaseComActivity` (extended by every activity) centralizes cross-cutting concerns: theming (a single fixed light theme), edge-to-edge system-bar insets, back-press handling (with a deliberate delay to let a full-screen ad finish first), and a global "every click may trigger an interstitial ad" touch-event interceptor. Firebase Analytics' **automatic screen tracking** (enabled by default in the Android SDK for `Activity`-based apps) is the only screen-view signal in the whole app — there is no manual `screen_view` logging anywhere.

### A.4 State management

There is no app-wide state management framework. State lives in three places:

1. `SharedPreferences`-backed singleton stores (`LauncherPreferences`, `ChargingSessionStore`, `PackageChangeEventStore`, `AdConfigRepository`'s own prefs) — this is the closest thing to a persistence layer.
2. Static/singleton manager classes with a listener pattern (`AdConfigRepository.get(context, url)`, `AdNetworkMonitor.get(context)`, `PaidTrafficEligibilityManager`) — process-wide singletons instantiated lazily, not through any DI framework.
3. Per-Activity instance fields for UI-local state.

### A.5 Networking / request layer

There is exactly **one** hand-rolled network client in the entire app: `AdConfigRepository`, which fetches a remote ad-configuration JSON document (served from a Cloudflare Worker, see `cloudflare-worker.js` / `ad-config.json` at the repo root) over `HttpURLConnection`. It is, by a wide margin, the most sophisticated piece of infrastructure code in the codebase:

- 1.5s connect/read timeouts, HTTPS-only URL validation (rejects non-`https`, userinfo, or fragment components)
- Up to 3 attempts with linear-ish backoff (`250ms << attempt`) on retryable failures (408/429/5xx, socket timeout)
- ETag-based conditional GET (`If-None-Match` → `304 Not Modified` short-circuits parsing)
- In-memory + `SharedPreferences`-backed disk cache, both keyed by a TTL the *server* controls (`RemoteAdConfig.getCacheTtlSeconds()`)
- A **stale-while-revalidate** window: a cached config up to 15 minutes old is still served if a live fetch fails
- **Fail-closed** beyond that window: if nothing usable is cached, ads are disabled rather than guessing
- Single-flight request coalescing (`requestInFlight` + a pending-callback list) so concurrent callers don't trigger duplicate fetches
- A periodic self-scheduling refresh loop that only runs while at least one listener is registered, plus a network-connectivity listener (`AdNetworkMonitor`) that triggers an immediate refresh once a validated network reappears after an outage

This pattern has nothing to do with analytics dispatch, but it is the best example in the repository of "what a resilient, offline-aware, network-backed component should look like on this platform," and it is directly reusable as a template if InfinityForge ever needs a remote-config/kill-switch component for tracking (see §5 and §E).

### A.6 Configuration / environment handling

Environment-specific values come from Gradle: `HDCAMERA_STORE_FILE`/`_PASSWORD`, `AD_CONFIG_URL`, `GMA_APP_ID` are read from Gradle properties or environment variables, with hard-coded production defaults baked into `build.gradle` as fallbacks. Build types (`release`, `minifiedQa`, `paidQa`) set a `FORCE_PAID_TRAFFIC` `BuildConfig` boolean, which is the only construct in the app that resembles an "environment" flag — and it governs ad-monetization test behavior specifically, not analytics environment tagging. **There is no `environment: development/preview/production` concept anywhere in the app's telemetry** — Firebase distinguishes environments at the project/App-ID level (a different Firebase project per build variant, configured outside this repo), not inside the event payload.

### A.7 Firebase / GA4 / Google Ads usage

- **Firebase Analytics**: initialized implicitly (`FirebaseAnalytics.getInstance(context)`); events logged via direct `logEvent(String, Bundle)` calls, no wrapper SDK beyond `BeautyAnalytics`/`AdTelemetry`.
- **Firebase Crashlytics**: gradle-plugin only. No `Crashlytics.log(...)`, `Crashlytics.recordException(...)`, or any manual non-fatal reporting call exists anywhere in the Java source — it is purely automatic fatal-crash capture.
- **Google Mobile Ads / Ad Manager**: the dominant subsystem. `GoogleAdUnit` models two providers (`ADMOB`, `AD_MANAGER_ADX`); AdMob revenue is auto-forwarded into Firebase by Google's own AdMob↔Firebase link (no app code needed), but **Ad Manager/AdX revenue is not**, so the app manually constructs and logs an `ad_impression` Firebase event for that path only (`AdRevenueAnalytics`).
- No GA4-specific API surface beyond what `firebase-analytics` already is (GA4 *is* the product `FirebaseAnalytics.logEvent` reports into).

### A.8 Authentication and identity handling

**None.** There is no login, no signup, no user account model, no auth SDK, no `setUserId`/`setUserProperty` call anywhere in the code. The closest concept to "identity" is device/install-scoped: `PaidTrafficEligibilityManager` resolves a boolean "is this a paid-acquisition install?" flag via the Play Install Referrer API, with its own small retry policy (1s, 3s delays, max 3 attempts per session), persisted in `SharedPreferences` and exposed to ad-serving logic. Firebase Analytics itself manages an anonymous App Instance ID under the hood, but the app never reads or reasons about it.

### A.9 Subscriptions / purchases / revenue

**No IAP or subscription code exists** — no Play Billing Library dependency, no purchase flow, no receipt validation. **100% of monetization is advertising.** "Revenue" in this app means ad revenue exclusively, handled entirely inside the `ads/` package (§A.10).

### A.10 Ad-related tracking

This is the richest part of the codebase and the part most relevant to the Metrics capability comparison in §3/§5:

- `AdTelemetry` — a process-wide, privacy-safe telemetry bridge. It is **decoupled from Firebase by a functional interface** (`Reporter`), wired to Firebase only once, in `LauncherApplication.onCreate()`: `AdTelemetry.setReporter(firebaseAnalytics::logEvent)`. This is, notably, the one piece of code in the whole app that already looks like a **provider adapter** in the InfinityForge sense.
- It reports a small, closed vocabulary of ad-lifecycle facts as three Firebase event names: `ad_runtime_event` (state machine over `request → loaded/load_failed`, `show_failed`, `paid`, plus ad-config fetch states), `ad_health_alert` (rate-limited operational alerts — slow load, failure streaks, fail-closed config, gate-watchdog releases), and `ad_impression` (the AdX/GAM-only manual revenue bridge described in §A.7).
- `AdHealthMonitor` converts raw telemetry into **rate-limited** alerts (a load-failure streak alert fires only at streak 3, then every 10th failure thereafter; a config fail-closed alert fires only once until recovery) — a deliberate anti-noise design.
- `AdRevenueAnalytics` is a small, pure, side-effect-free module that turns a Google `AdValue` callback into a normalized `{value, currency, ad_source, ad_format, ad_unit_id}` shape before it is logged — structurally almost identical to what `recordMetric("ad_revenue", ...)` would look like under the InfinityForge contract.
- All of this dispatch is thread-hopped onto the main `Looper` if called from a background thread (`AdTelemetry.dispatch`) — this is a thread-affinity guard, not an offline queue.

### A.11 Screen / lifecycle tracking

Entirely implicit. Firebase Analytics' automatic screen-tracking feature (on by default for Android) is the only screen signal — it reports the Activity's Java class name as the screen, not an application-chosen stable identifier. There is no app-level `logScreenView` call, no de-duplication logic, and no `previous_screen` concept anywhere in the code.

### A.12 Error / crash tracking

Crashlytics captures fatal crashes automatically via the Gradle plugin. There is **no handled-error / non-fatal telemetry** anywhere — no equivalent of `handled_error` from the InfinityForge metric taxonomy exists in this app today, despite the app clearly having recoverable failure paths (ad load failures, config fetch failures) that are already being *detected* (`AdHealthMonitor`) but are only ever turned into ad-specific alerts, never into a general-purpose reliability signal.

### A.13 Tracking abstractions / services

Exactly two purpose-built classes:

1. **`BeautyAnalytics`** (`analytics/BeautyAnalytics.java`) — a `final` class with six static methods (`logCameraOpen`, `logPhotoCaptured`, `logEditorOpen`, `logEditSaved`, `logVideoSaved`, `logGalleryOpen`), each building its own `Bundle` and calling `FirebaseAnalytics.getInstance(context.getApplicationContext()).logEvent(...)` directly. Every event gets one shared tag, `app_module: "beauty_studio"`. There is no shared envelope, no schema, no validation, no snake_case enforcement, no versioning — each method is its own ad hoc contract, enforced only by the Java compiler at the call site, not by any runtime check.
2. **`AdTelemetry`** (§A.10) — decoupled from Firebase via `Reporter`, otherwise similarly ad hoc.

### A.14 How events are created, transformed, and dispatched

There is no event object, no builder, no transformation pipeline. Call sites build an Android `Bundle` inline, pass it straight into `FirebaseAnalytics.logEvent(String, Bundle)`, and the call returns immediately — dispatch, batching, retry, and offline persistence for the *event itself* are entirely inside the closed-source Firebase Analytics SDK, invisible to and unmanaged by this codebase. The app never queues, retries, or persists an event on its own. The only place the app does its own queuing/retry/persistence is the unrelated ad-config fetch (§A.5).

### A.15 Async behavior

Two distinct async patterns exist, and they should not be confused with each other:

- **Thread-affinity hopping** (`AdTelemetry.dispatch`, `AdConfigRepository`'s `runOnMain`): ensures a call lands on the main `Looper` regardless of caller thread. This is about thread safety, not resilience.
- **Real async I/O with retry** (`AdConfigRepository.refreshWithRetry`, on a dedicated single-thread `ExecutorService`): the only place in the app doing genuine network resilience engineering.

---

## B. Reference app tracking / request flow

### B.1 App launch

```
Process starts
    -> LauncherApplication.onCreate()
         -> AdActivityBackdropInstaller.install(this)
         -> FirebaseAnalytics.getInstance(this)        [implicit SDK init; Firebase auto-logs
                                                          first_open / app_open — no app code involved]
         -> AdTelemetry.setReporter(firebaseAnalytics::logEvent)   [wires the one provider adapter]
         -> PaidTrafficEligibilityManager.resolveFromPlayInstallReferrer()
                -> InstallReferrerClient.startConnection(...)
                     -> onInstallReferrerSetupFinished(OK)
                          -> PaidTrafficReferrerParser.findPaidClickIdentifier(referrer)
                          -> persist is_paid_traffic_user + install_referrer_processed to SharedPreferences
                     -> (FEATURE_NOT_SUPPORTED / DEVELOPER_ERROR) -> persist "not paid", resolved
                     -> (transient failure) -> retry after 1s, then 3s, up to 3 attempts total
    -> SplashComActivity launches (LAUNCHER intent-filter)
         -> AdConfigRepository.get(context, AD_CONFIG_URL).getConfig(callback)
              -> memory-fresh?  -> return cached config immediately
              -> else           -> HTTP GET (ETag) on background executor, up to 3 attempts w/ backoff
                                 -> on success/stale/fail-closed, deliver config + fire AdTelemetry.config(...)
    -> LaunchHomeComActivity (HOME/DEFAULT intent-filter) becomes the resumed screen
         -> Firebase auto-logs a screen_view for this Activity (no app code)
```

**What actually happens at each conceptual step**, mapped onto the prompt's requested "Application Action → Tracking/Event API → Validation/Transformation → Metadata/Identity → Provider → Analytics Platform" shape:

| Step | Reference app reality |
|---|---|
| Application Action | Process cold-starts; `Application.onCreate()` fires |
| Tracking/Event API | None called directly for "app launch" — Firebase's SDK auto-instruments this from `Application`/`Activity` lifecycle callbacks it hooks internally |
| Validation/Transformation | None — app never sees or shapes this event |
| Metadata/Identity | Firebase's own opaque App Instance ID; no app-level identity call |
| Provider | Firebase Analytics SDK (already initialized by manifest content-provider auto-init) |
| Analytics Platform | GA4 backend |

Attribution (`PaidTrafficEligibilityManager`) is a **parallel, unrelated** identity-adjacent flow — it never touches Firebase Analytics at all; it only sets a local flag that ad-serving code reads later.

### B.2 Screen navigation

```
User taps a home-screen icon / in-app button
    -> startActivity(Intent) to a *ComActivity
         -> BaseComActivity.onCreate()
              -> theme/system-bars setup, back-press handler, every-click ad interceptor init
         -> Activity.onResume()
    -> Firebase's auto screen-tracking observes the Activity transition
         -> logs `screen_view` with `firebase_screen` = Activity's class-derived name (Firebase default),
            `firebase_screen_class`, and its own auto-generated `firebase_screen_id`
```
No app code participates. There is no `screen_name` chosen by the application, no dedup policy, and no `previous_screen` — this is the single biggest structural gap versus `screen-tracking.md`.

### B.3 Login / signup

**Does not exist in this app.** There is no such flow to trace.

### B.4 Feature usage (Beauty Studio funnel)

```
User taps "Camera" tool in Beauty Studio
    -> BeautyStudioComActivity (toolMode == TOOL_CAMERA)
         -> BeautyAnalytics.logCameraOpen(this)
              -> Tracking/Event API: BeautyAnalytics.log(context, "beauty_camera_open", null)
              -> Validation/Transformation: none — safe(null) coercion only applied to string params,
                 not applied here since parameters == null; a single "app_module: beauty_studio" tag
                 is unconditionally merged in
              -> Metadata/Identity: none set by app code — Firebase attaches its own envelope
                 (app instance id, timestamp, app version, OS) invisibly
              -> Provider: FirebaseAnalytics.getInstance(applicationContext).logEvent(...)
              -> Analytics Platform: GA4 backend

User captures a photo
    -> BeautyStudioComActivity -> BeautyAnalytics.logPhotoCaptured(this, captureType, itemCount)
         -> Bundle{capture_type: safe(captureType), item_count: max(1, itemCount), app_module: "beauty_studio"}
         -> FirebaseAnalytics.logEvent("beauty_photo_capture", bundle)
```
This is the cleanest, most InfinityForge-shaped flow in the app: a named event with typed, bounded properties. It is still missing an envelope, schema_version, and any validation beyond ad hoc null-coercion.

### B.5 Purchase / subscription

**Does not exist.** No purchase or subscription code anywhere in the repository.

### B.6 Ad impression / ad revenue

```
Ad SDK fires OnPaidEventListener callback (AdValue value, ResponseInfo responseInfo)
    -> AdTelemetry.revenue(placement, format, adUnit, value, responseInfo)
         -> Tracking/Event API: builds base Bundle {placement, format, state:"paid", provider}
              + value_micros, currency, precision, adapter, response_id
         -> Validation/Transformation: AdRevenueAnalytics.shouldLogManualAdImpression(adUnit)
              gates whether a SECOND, normalized event is also emitted — only for AD_MANAGER_ADX,
              because AdMob's own revenue already reaches Firebase automatically via Google's own
              AdMob<->Firebase link, so logging it again here would double-count it
         -> if gated true: AdRevenueAnalytics.create(valueMicros, currency, adSource, format, adUnitId)
              -> validates currency is a well-formed 3-letter code, valueMicros >= 0
              -> normalizes value_micros/1_000_000 into a decimal major-unit value
              -> Metadata/Identity: none app-specific; ad_platform = "Google Ad Manager" tag added
              -> Provider: AdTelemetry.dispatch("ad_impression", analyticsParameters)
                   -> Reporter (== firebaseAnalytics::logEvent, wired at Application.onCreate)
              -> Analytics Platform: GA4 backend, under a raw event named literally "ad_impression"
         -> Regardless of the gate: the RUNTIME_EVENT_NAME ("ad_runtime_event") is always dispatched
              too, and AdHealthMonitor.onLoaded(...) is invoked for load-latency alerting
```
This is the closest thing in the whole codebase to a genuine value+unit+source **Metric** as InfinityForge defines it — it just happens to be shipped today as a bare Firebase Bundle event with no schema.

### B.7 Logout

**Does not exist** — no identity to log out of.

### B.8 Error

```
Ad load fails
    -> GoogleAdUnit / loader callback -> AdTelemetry.loadFailure(placement, format, adUnit, error,
        latencyMs, retryAttempt)
         -> Tracking/Event API: base Bundle + latency_ms, error_code, error_domain, retry_attempt,
              adapter/response_id if available
         -> Provider: dispatch("ad_runtime_event", parameters) via the same Reporter bridge
         -> AdHealthMonitor.onLoadFailure(placement, format, error.getCode())
              -> increments an in-memory failure-streak counter (keyed by placement:format)
              -> at streak==3, and every 10th failure after, AdTelemetry.alert(...) fires a SEPARATE
                 "ad_health_alert" event, itself rate-limited to avoid alert storms
```
This is ad-specific error handling, well engineered, but entirely disconnected from any general-purpose "handled error" concept — a crash in, say, the photo editor or gallery would only ever reach Crashlytics as a fatal, or nowhere at all if caught and swallowed.

---

## C. Current InfinityForge architecture

### C.1 What actually exists on disk

```
infinityforge-tracking-module/
├── README.md, CONTRIBUTING.md, CHANGELOG.md         (governance)
├── specification/            15 Markdown files, ~1,190 lines total — the normative contract
├── events/                   5 YAML files — 14 canonical events, machine-readable
├── metrics/                  5 YAML files — 8 canonical metrics, machine-readable
├── schema/                   5 YAML files — JSON-Schema-flavored envelope/type definitions
├── examples/                 22 example JSON payloads (events + metrics)
├── docs/implementation-guide.md   — guidance for adapter authors, no code
└── validation/validate.py    416 lines — lints the SPEC repo itself, not runtime events
```
**Total: 0 lines of adapter/SDK code, in any language.** This is by explicit design (README §5, "What does NOT belong here": *"Any platform-specific SDK or adapter code ... never in this repository"*), not an oversight.

### C.2 The tracking contract, as specified

| Concept | Specified as |
|---|---|
| Core operations | 6 required: `initialize`, `track`, `identify`, `setUserProperties`, `screen`, `reset` — plus 1 optional, additive: `recordMetric` |
| Event envelope | 9 required fields (`event`, `schema_version`, `timestamp`, `app_id`, `environment`, `platform`, `sdk_version`, `app_version`, `anonymous_id`) + 2 optional (`sdk_name`, `user_id`) + `properties` |
| Metric envelope | 11 required fields (`metric_name`, `schema_version`, `value`, `unit`, `source`, `timestamp`, `app_id`, `environment`, `platform`, `sdk_version`, `app_version`, `anonymous_id`) + optional (`sdk_name`, `user_id`, `currency`, `reference_id`, `dimensions`) |
| Event taxonomy | 14 canonical events across 5 categories: application (`app_opened`, `screen_viewed`), authentication (`signup_started/completed`, `login_started/completed`), onboarding (`onboarding_started/completed`), product (`feature_used`), monetization (`paywall_viewed`, `trial_started`, `subscription_started`, `subscription_cancelled`, `purchase_completed`) |
| Metric taxonomy | 8 canonical metrics across 5 categories: monetization (`revenue`), advertising (`ad_impression`, `ad_revenue`), engagement (`session_duration`), performance (`app_launch_duration`, `screen_load_duration`, `operation_duration`), reliability (`handled_error`) |
| Identity | `anonymous_id` (SDK-managed, survives restart, replaced — never reused — on `reset`) + `user_id` (app-managed via `identify`, cleared by `reset`) |
| Screen semantics | `screen_name` required, stable/logical (never dynamic/PII), consecutive-duplicate suppression required, `previous_screen` optional |
| Metadata ownership | An explicit table stating who supplies each field — app vs. SDK — for both envelopes |
| Environment | Exactly `development` / `preview` / `production`, with a narrowly scoped, documented fallback rule for dev-mode detection only |
| Privacy | A closed list of prohibited categories (secrets, payment data, unnecessary PII), a review-and-approval process for exceptions, and metric-specific rules (dimension cardinality, `reference_id`/`error_code` opacity) |
| Errors | Never crash, never block, isolate provider failures, correct→drop→queue in that preference order, dev diagnostics required, no PII in prod diagnostics |
| Versioning | 3 levels (contract semver — currently **1.2.0** — per-event/metric `schema_version`, adapter `sdk_version`), an explicit compatible-vs-breaking table, a deprecation process |
| Explicitly out of scope | Transport, batching, retry, storage mechanism, provider selection, delivery guarantees, cross-network ordering, backend-side deduplication |
| Explicitly rejected (documented, not silently omitted) | Crash modeling, notification metrics, a generic attribution/acquisition metric, a generic conversion metric, on-device derived metrics (DAU, LTV, MRR, eCPM, ROAS, …) |

### C.3 Documented vs. actually implemented

| Area | Documented | Actually implemented |
|---|---|---|
| Six core operations | Fully specified, field-by-field | Not implemented anywhere — no `track()`, no `identify()`, nothing callable |
| Event/metric envelope | Full JSON-Schema-flavored YAML | Not enforced anywhere at runtime — `validate.py` checks the *definition files*, never a live payload |
| Identity model | Fully specified lifecycle | No code manages an `anonymous_id` or `user_id` anywhere in this repo (correctly — that's an adapter's job — but it means "identity" today is 100% aspirational) |
| Provider abstraction | Described conceptually (`Contract → Adapter → Provider → Firebase/GA4/Other`) | No adapter and no provider integration exists to abstract |
| Error isolation | Six non-negotiable rules | No runtime to enforce them in — nothing to test |
| Metrics capability | A 294-line normative document plus envelope/taxonomy/derived-metrics docs — the most thoroughly specified part of the whole repo | Same as above: zero lines of code |
| Validation | A described set of malformed-payload rules (`errors.md` §"What counts as malformed") | Implemented only as *repository linting* (`validate.py`), and only against the YAML/JSON files living in this repo — there is no reusable validator an adapter could import to check a live event before sending it |

**In short: nothing in this repository is "implemented" in the sense the reference app's code is implemented.** Everything under `specification/`, `events/`, `metrics/`, `schema/` is a very precise design document; `validate.py` is a documentation-quality gate, not a tracking runtime.

---

## D. Comparison table

| Area | Reference App | InfinityForge | Gap | Recommendation |
|---|---|---|---|---|
| Event model | Ad hoc `Bundle` per call site, 6 app-specific events + ~3 ad-lifecycle event names, no schema, no versioning | 14 canonical events, `snake_case`, typed/required properties, `schema_version` per event | Reference app events don't map to any canonical InfinityForge event name; they're all "app-specific" by the contract's own definition | When a Kotlin/Android adapter is built, route Beauty Studio's `feature_used`-shaped occurrences (camera open, editor open, gallery open) through the canonical `feature_used` event with a `feature_name` property, instead of one bespoke event name per action — the contract already has the right shape for this |
| Request/dispatch model | Fire-and-forget `logEvent(Bundle)`; batching/retry/offline entirely inside the closed-source Firebase SDK | Explicitly out of scope by design ("Transport... is not specified") | None — the contract's choice to leave this open is *validated*, not contradicted, by the reference app: the app never reimplements what its provider already does well | Adapters should default to "let the provider SDK batch/retry/persist" exactly as the reference app does, and only build their own dispatcher/queue when talking to a provider that doesn't (see §5) |
| Identity | No `user_id` concept at all (no accounts); a parallel, unrelated "paid traffic" boolean from Install Referrer, persisted in `SharedPreferences` with its own bespoke retry (1s/3s, 3 attempts) | Full `anonymous_id`/`user_id` lifecycle, `reset` issues a *new* `anonymous_id` for privacy | The reference app has no code path exercising `identify`/`reset` at all — this is untested territory for InfinityForge's identity rules | Any pilot adapter needs a dedicated identity-lifecycle test even though the reference app can't provide one; the app's existing `SharedPreferences`-backed persistence pattern (see `PaidTrafficEligibilityManager`) is a reasonable, already-proven template for persisting `anonymous_id` across restarts |
| Session/lifecycle | No explicit session boundary; Firebase manages `app_open`/session internals invisibly | `session_duration` metric exists, but the contract deliberately does not define a session boundary, leaving it to the implementation | Reference app offers no session-boundary logic to borrow | An adapter must define foreground/background session boundaries itself (contract explicitly punts this); recommend a simple inactivity-timeout model consistent across platforms even though the contract won't mandate one |
| Screen tracking | 100% delegated to Firebase's automatic Activity-based `screen_view` — raw class names, no dedup, no `previous_screen` | Explicit `screen_name` (app-chosen, stable, non-PII), required consecutive-dedup, optional `previous_screen` | Direct conflict: Firebase's auto screen name is not a stable app-chosen identifier and the app never suppresses duplicates itself | An InfinityForge Kotlin adapter must NOT rely on Firebase automatic screen tracking to satisfy `screen()` — it needs its own navigation-observer (Activity/Fragment lifecycle hook or Compose `NavController` listener) feeding `screen()` explicitly, with its own dedup state machine |
| Validation | Only ad hoc null→"unknown" string coercion in `BeautyAnalytics.safe()`; `AdTelemetry` truncates long strings; nothing else | A full, explicit malformed-payload rule set (`errors.md`) with a correct→drop→queue order of preference | The reference app has no general validation layer, no dev-mode diagnostics for bad events, nothing resembling the contract's error rules | This is the single highest-leverage piece of *new* code to write: a small, dependency-light runtime validator, closely mirroring `validate.py`'s existing rule set but running against live payloads inside the adapter, in every language |
| Metadata | None explicit — Firebase attaches its own opaque envelope (App Instance ID, timestamp, platform, app version) that the app never reads or reasons about | An explicit, fully-owned envelope with a field-by-field ownership table (app vs. SDK) | The reference app cannot demonstrate an explicit envelope because Firebase hides its own | Adapters must build and own this envelope themselves before calling into any provider — it should exist as a genuine in-memory/JSON object, not be assumed to come from the provider |
| Provider abstraction | One hard dependency: `FirebaseAnalytics.getInstance(context)` called directly from two places; the *only* abstraction anywhere is `AdTelemetry.Reporter`, a one-method functional interface wired once at startup | `Contract → Platform Adapter → Provider Adapter → Firebase/GA4/Other`, provider named nowhere in the contract itself | The reference app is tightly coupled to Firebase everywhere except the one `AdTelemetry.Reporter` seam | `AdTelemetry.Reporter` is a genuinely good, minimal pattern — generalize it: a platform adapter should depend on a small provider-interface type (`report(event/metric envelope)`), never call a vendor SDK directly from business/UI code, and wire the concrete provider once at composition root exactly as `LauncherApplication.onCreate()` already does for ads |
| Firebase/GA4 compatibility | Fully compatible by construction — it *is* Firebase Analytics | Provider-agnostic by design; Firebase is one of several "providers an implementation might eventually integrate with," named only in `docs/implementation-guide.md` | None structurally; the contract's envelope maps cleanly onto a Firebase `Bundle` (properties → Bundle key/values, envelope fields → either Bundle keys or Firebase's own implicit fields) | A Firebase provider adapter is a small, mechanical translation layer — this is low-risk, well-understood work once the platform adapter exists |
| Ads/monetization | Extremely mature: `ad_runtime_event` state machine, rate-limited `ad_health_alert`, a real `ad_impression` revenue bridge with currency validation and micros→major-unit conversion | `ad_impression` (fixed `value:1`) and `ad_revenue` (currency-required) canonical metrics, explicitly modeled on exactly this kind of measurement | The two line up almost 1:1 in substance; the gap is purely representational — reference app emits these as bare Firebase *events*, not as the distinct **Metric** primitive the contract defines | This is the strongest evidence in the whole analysis that the Metrics capability is *necessary*, not speculative. `AdRevenueAnalytics.create(...)` should become close to a direct model for `recordMetric("ad_revenue", ...)`; `AdHealthMonitor`'s rate-limiting logic is a good pattern to keep at the adapter layer (not something the contract needs to specify) |
| Async behavior | Two distinct, well-separated concerns: main-thread hopping (thread safety) vs. `ExecutorService`-based retrying I/O (resilience) — never confused with each other | `track`/`screen`/`recordMetric` are explicitly "fire-and-forget from the calling application's perspective" — matches the reference app's calling convention exactly | None — this is a case of strong alignment | Preserve the fire-and-forget contract in every adapter; do the same main-thread/background-thread separation the reference app already models cleanly |
| Queue/retry/offline | Fully implemented, but *only* for the ad-config fetch (§A.5) — never for analytics events themselves, which are delegated wholesale to Firebase's internal queue | Explicitly out of scope for the contract ("this contract does not specify how a measurement is queued, retried, or delivered while the device is offline") | None — again, strong alignment. The reference app independently arrived at "don't reinvent what the provider already does" | Do not build a general-purpose offline event queue inside a platform adapter that wraps a batching provider SDK (Firebase, Amplitude, etc.) — it would duplicate reliability logic the provider already has, tested at far larger scale. Reserve real retry/backoff/stale-cache engineering (`AdConfigRepository`'s pattern) for adapter-owned network calls that have no provider SDK underneath them — e.g., a custom InfinityForge backend, or a remote sampling/kill-switch config |
| Duplicate events | Not solved by the app for analytics events (relies on ad SDK callback semantics + AdMob's own dedup); solved only for ad-config change notifications (a `publishChange` debounce) | `reference_id` (metrics) / `transaction_id` (monetization events) exist purely so a *downstream* system can dedupe; the contract explicitly does not mandate SDK-side dedup | Consistent — neither side does SDK-level dedup, and the contract's rationale (dedup needs a stable ID from the *source system*, which not every measurement has) matches what the reference app's ad SDK integration actually looks like | Keep dedup out of the adapter's runtime logic; make sure every canonical event/metric that plausibly needs it (purchases, subscriptions, ad revenue) always has a place to carry a stable id — the contract already added `transaction_id` for exactly this reason in 1.2.0 |
| Ordering | Not addressed; Firebase's own queue is assumed reliable | Explicitly a non-goal; `timestamp` is captured at call time regardless of transmission order | None | No action needed — this is a correctly-scoped non-goal on both sides |
| Provider failures | Isolated per-provider by construction, because there is exactly one provider; a `Reporter == null` check in `AdTelemetry.dispatch` silently no-ops if the reporter was never wired | Rule 4 in `errors.md`: a failure in one provider must not affect delivery to any other, or the app | Reference app has never had to solve the *multi-provider* isolation problem, because it only ever has one provider | Multi-provider fan-out (§C.2's "Firebase, Amplitude, custom InfinityForge backend, or other") needs an actual isolation layer (e.g., each provider call wrapped in its own try/catch, none blocking on another) that the reference app cannot demonstrate — this must be built and tested fresh |
| Performance | Ad-config fetch instrumented for `latency_ms` inline as part of `ad_runtime_event`/`config` telemetry; nothing else timed | `app_launch_duration`, `screen_load_duration`, `operation_duration` canonical metrics | The one latency measurement that exists in the reference app (`AdConfigRepository`'s fetch latency) is *exactly* the shape `operation_duration` was built for (`dimensions.operation`), but it is currently folded into an ad-specific event instead | Worth calling out to the app team directly: today's `latency_ms` parameter on `ad_runtime_event`/`config` states is a real, live example of a measurement InfinityForge's `operation_duration` metric (with `dimensions.operation: "ad_config_fetch"`) already models correctly — this is a concrete illustration for the implementation guide |
| Privacy | Reasonably careful in practice (truncated strings, `safe()` null-coercion, no PII spotted in any event property observed) but with **no policy encoded anywhere in code** — nothing would stop a future contributor from adding a raw user string to a `Bundle` | An explicit prohibited-category list, a mandatory review process for exceptions, and metric-specific opacity rules for `reference_id`/`error_code` | The reference app's privacy safety today is a property of the current developers' care, not of any enforced mechanism | A runtime validator (see Validation row above) is also the natural enforcement point for privacy rules that *can* be checked structurally (e.g., rejecting values that look like emails/tokens in specific known-risky property names) — full semantic privacy enforcement can't be automated, but structural guardrails can |

---

## E. Recommended target architecture

### E.1 What should remain unchanged

The contract content itself — `specification/`, `events/`, `metrics/`, `schema/` — should not be redesigned. It is already disciplined in a way that is easy to underestimate on first read: it explicitly evaluated and **rejected** scope creep in several places (crash modeling, a generic notification metric, a generic attribution metric, a generic conversion metric, on-device derived metrics), and its Metrics capability (added in contract version 1.2.0, per `versioning.md`) already anticipates, almost field-for-field, the ad-revenue/impression telemetry the reference app hand-builds today. The six-plus-one operation model, the envelope, the identity lifecycle, the privacy rules, the error rules, and the versioning rules are all sound and should ship as-is into the first adapter.

### E.2 What is missing (not what's wrong — what doesn't exist yet)

1. **Any adapter at all.** This is the actual blocker, not a design flaw in the contract. Recommend building **one pilot adapter first** — Kotlin/Android is the natural first choice precisely because this reference app already exists as a real Android/Firebase/AdMob environment to validate against.
2. **A runtime payload validator.** `validate.py`'s rule set (§errors.md's "what counts as malformed," almost verbatim) should be ported into a small, dependency-light, per-language validation routine that every adapter runs on every `track`/`screen`/`recordMetric` call before handing the payload to a provider. This is the most direct way to make the contract's error-handling rules real instead of aspirational.
3. **A generalized provider-adapter interface**, modeled on `AdTelemetry.Reporter` but covering the full envelope (events and metrics), not just ad Bundles.
4. **An implementation-guide "cookbook" section** mapping common provider/SDK callback shapes (a billing library's purchase callback, an ad mediation SDK's impression/revenue callback, a crash reporter's non-fatal-error hook) onto the six operations and `recordMetric` — using the reference app's `AdRevenueAnalytics`/`AdTelemetry` as a concrete worked example.
5. **Explicit acknowledgment, at the adapter-guidance level, of a "config/kill-switch" concern** the contract correctly leaves out of scope but that real InfinityForge apps will need (the reference app's `AdConfigRepository` is proof): a way for an adapter to fetch a remote sampling rate or kill switch for tracking itself. This does not belong in the contract (it isn't a tracking concept), but it deserves a short, explicit note in `docs/implementation-guide.md` so platform teams don't each invent it differently — recommend reusing the retry/backoff/ETag/stale-cache/fail-closed shape of `AdConfigRepository` almost verbatim, since it is already a proven, production-hardened pattern for exactly this kind of problem.

### E.3 What is unnecessarily complex

Very little, on the contract side. If anything, the risk is the opposite direction: because the contract is unimplemented, there is a temptation for the *first* adapter to over-build (a full offline event queue, a generic multi-provider batching engine, a custom retry framework for events) when the reference app's own lived experience says the opposite: **let the provider SDK do provider-side reliability engineering; only build your own resilience code for network calls that have no provider SDK underneath them.**

### E.4 Layer responsibilities

```
                         Common Tracking Contract
        (specification/, events/, metrics/, schema/ — THIS repo, unchanged)
     6 operations + recordMetric | envelope | identity | privacy | errors | versioning
                                   |
                                   v
                          Platform Adapter
        (React Native / Swift / Kotlin — a NEW repo/package per platform)
   Responsible for:
     - implementing the 6+1 operations in an idiomatic calling convention
     - building and stamping the envelope (timestamp, platform, sdk_name/version,
       app_version, anonymous_id/user_id) before anything reaches a provider
     - identity persistence + lifecycle (identify/reset, new anonymous_id on reset)
     - screen-context tracking + duplicate suppression (own navigation-layer hook —
       NOT delegated to a provider's automatic screen tracking)
     - session-boundary definition (foreground/background or inactivity timeout)
     - runtime payload validation (port of validate.py's malformed-payload rules)
     - error containment: every operation wrapped so nothing can throw into app code
     - dev-mode diagnostics (malformed/unknown event & metric logging) vs. prod silence
                                   |
                                   v
                          Provider Adapter(s)
      (small, swappable, one per analytics/ads/billing vendor the platform adapter
       talks to — Firebase today, potentially others later)
   Responsible for:
     - translating the normalized envelope + properties/dimensions into the
       provider's native call shape (e.g., Bundle for FirebaseAnalytics.logEvent)
     - isolating its own failures from every other registered provider
     - either delegating batching/retry/offline entirely to the provider's own SDK
       (the default, and what the reference app already does for Firebase), or,
       ONLY when the provider has no SDK (e.g., a bespoke InfinityForge ingestion
       endpoint), implementing its own retry/backoff/offline layer modeled on
       AdConfigRepository
                                   |
                                   v
                     Firebase / GA4 / Other Providers
```

### E.5 Repository / module structure

```
infinityforge-tracking-module/            (this repo — UNCHANGED in scope, minor additions)
├── specification/  events/  metrics/  schema/  examples/  docs/    (as today)
└── validation/
    ├── validate.py                        (unchanged — repo/spec linter)
    └── runtime/                            (NEW — reference validation logic, language-neutral
        └── malformed-payload-rules.md       pseudocode + a JSON description of every rule in
                                              errors.md §"What counts as malformed", so every
                                              adapter's runtime validator can be generated/ported
                                              from ONE source instead of copy-pasted three times)

infinityforge-android-tracking/            (NEW — pilot adapter, Kotlin)
├── core/           six operations + recordMetric, envelope builder, identity store,
│                   screen dedup, session boundary, runtime validator (ported from the
│                   shared rules above), error containment wrappers
├── providers/
│   └── firebase/   FirebaseProviderAdapter — translates envelope -> Bundle -> logEvent
├── testkit/        an in-memory "TestProvider" for adapter/unit tests, and a conformance
│                   test suite that runs docs/implementation-guide.md's checklist
│                   automatically (identity lifecycle, screen dedup, malformed-input
│                   handling, privacy-category rejection, etc.)
└── sample-app/     wired into a throwaway app (or, ambitiously, a fork of the Beauty
                    Studio module) to prove the adapter under real Firebase/AdMob traffic

infinityforge-rn-tracking/                 (FUTURE — same shape as above, once a real RN
                                            reference app exists to validate against — see §H)

infinityforge-swift-tracking/              (FUTURE — same shape, once a Swift adapter is
                                            prioritized)
```

### E.6 Cross-platform guarantee, worked through one event

`purchase_completed` on three platforms, same meaning, different code:

- **RN adapter**: JS call `track('purchase_completed', { product_id, price, currency, quantity, transaction_id })` → adapter stamps envelope → validator checks required `product_id` present, `price`+`currency` paired → Firebase provider adapter calls the RN Firebase Analytics module's `logEvent`.
- **Swift adapter**: native call (however the adapter names it) with the same logical fields → same envelope/validation → `FirebaseAnalytics.logEvent(_:parameters:)`.
- **Kotlin adapter**: same shape → `FirebaseAnalytics.getInstance(context).logEvent("purchase_completed", bundle)` — i.e., exactly the call `BeautyAnalytics` already makes today, just reached through a generic, validated, envelope-stamping path instead of a bespoke one-off method.

The wire-level JSON that eventually reaches GA4/Firebase is identical in shape across all three, because the envelope and the event definition are owned by the contract, not by any adapter.

---

## F. Required changes — specific files/modules/APIs

These are concrete next steps, not abstract recommendations:

1. **New file, this repo**: `validation/runtime/malformed-payload-rules.md` (or `.json`) — extract `errors.md`'s "What counts as malformed" (events) and its metrics subsection into a single, language-neutral rule list that every adapter's runtime validator implements identically. Today that rule set exists only as prose in `errors.md` plus a Python-only implementation in `validate.py` that checks the wrong thing (spec files, not payloads).
2. **New repository**: `infinityforge-android-tracking` (or equivalent name), implementing the module structure in §E.5. This is the single highest-priority piece of work — without it, "can the tracking module support an app like the reference app" cannot be answered by anything other than "not yet."
3. **New file in the new adapter repo**: `providers/firebase/FirebaseProviderAdapter.kt`, generalizing the pattern already proven in `Messages-Home-Source-v1.0`'s `ads/AdTelemetry.java` (`Reporter` interface) to the full envelope, not just ad Bundles.
4. **New file in the new adapter repo**: a screen-tracking observer (an `Application.ActivityLifecycleCallbacks` implementation, or a Compose navigation listener) that calls `screen(screen_name, ...)` explicitly and owns duplicate suppression — replacing reliance on Firebase's automatic screen tracking, which the reference app currently uses and which does not satisfy `screen-tracking.md`.
5. **Amend `docs/implementation-guide.md`** (this repo) to add a short "Metrics cookbook" subsection: a worked example mapping an ad mediation SDK's `OnPaidEventListener`-style callback onto `recordMetric("ad_revenue", ...)`/`recordMetric("ad_impression", ...)`, directly informed by `AdRevenueAnalytics.java`'s existing logic (currency validation, micros→major-unit conversion, the AdMob-vs-AdX double-counting guard). This turns an abstract capability into a copy-pasteable pattern for the next platform team.
6. **Amend `docs/implementation-guide.md`** with a short, clearly-scoped note (not a contract change) that a platform adapter needing a remote sampling/kill-switch for tracking itself should model it on a resilient fetch-with-fallback pattern (retry+backoff, conditional GET/ETag if the transport supports it, a stale-but-usable cache window, fail-closed beyond that window) — citing `AdConfigRepository.java` as a proven reference implementation of that shape, without importing any of its ad-specific code.
7. **No changes needed** to `specification/`, `events/*.yaml`, `metrics/*.yaml`, or `schema/*.yaml` at this time — every gap found traces back to "not implemented yet," not "specified incorrectly."

---

## G. Cross-platform strategy

The contract already satisfies the "no framework/vendor/language" test — `validate.py` enforces this mechanically today by scanning `specification/`, `events/`, `metrics/`, `schema/`, and `examples/` for a hard-coded forbidden-term list (`firebase`, `crashlytics`, `amplitude`, `mixpanel`, `posthog`, `segment`, `rudderstack`, `admob`, `revenuecat`, `google analytics`, `expo router`, `react navigation`, `swiftui`, `uikit`, `jetpack compose`, and more) and fails the build if any leak in. This is a genuinely strong, currently-enforced guarantee — nothing in this analysis found a violation of it.

What has to be **abstracted at the adapter layer**, per platform, so the same event means the same thing everywhere:

| Concern | RN adapter's job | Swift adapter's job | Kotlin adapter's job |
|---|---|---|---|
| Screen detection | Hook React Navigation's (or whatever router is chosen) state-change listener | Hook `UIViewController` lifecycle or SwiftUI `.onAppear`, app's choice | Hook `Application.ActivityLifecycleCallbacks` or Compose nav listener — reference app shows the Activity-lifecycle version is straightforward to build |
| Identity persistence | AsyncStorage / MMKV, app's choice | Keychain or UserDefaults, app's choice | `SharedPreferences` or DataStore — reference app's `PaidTrafficEligibilityManager`/`LauncherPreferences` are a proven template for this exact persistence shape |
| Thread/queue model | JS event loop + a native bridge hop if needed | GCD | `Looper`/`Handler` or coroutines — reference app's `AdTelemetry.dispatch` main-thread-hop pattern is directly reusable |
| Provider SDK call | `@react-native-firebase/analytics`'s `logEvent` | `FirebaseAnalytics.logEvent(_:parameters:)` | `FirebaseAnalytics.getInstance(context).logEvent(String, Bundle)` — exactly what the reference app calls today |
| Build-time environment signal | Metro/bundler dev-mode flag (`__DEV__`), per `metadata.md`'s documented fallback exception | Xcode build configuration | Gradle build type/flavor — the reference app's `BuildConfig.FORCE_PAID_TRAFFIC` pattern shows the mechanism (a Gradle-injected `BuildConfig` field), though it's used for a different flag today |

None of these need to be, or should be, specified inside `infinityforge-tracking-module` itself — they are exactly the kind of "platform-specific how" the contract deliberately stays silent on (`overview.md`: *"no method signature, no class name, no import statement anywhere in this specification"*). The same `purchase_completed` event, with the same envelope shape and the same required fields, is fully achievable on all three platforms using entirely different underlying navigation/storage/threading primitives — which is precisely the guarantee `contract.md`'s "Cross-platform guarantees" section promises.

---

## H. Final verdict

> **Can the improved InfinityForge Tracking Module support an application similar to the reference app today, while also remaining suitable for future React Native, Swift and Kotlin applications?**

**Not today — but not because anything about the contract is wrong.** The contract is well-designed, disciplined, internally consistent, and — based on a direct, line-by-line comparison against a real, ad-monetized, Firebase-instrumented Android app — already anticipates almost every real-world telemetry shape that app actually needs, including the trickiest one (ad revenue/impression normalization, via the Metrics capability). What's missing is not design work; it's **implementation**. There is currently no code anywhere — in this repository or otherwise — that a team could import into an app and call `track()` on. An app team building something like `Messages-Home-Source-v1.0` today has no choice but to do exactly what that app's authors did: call `FirebaseAnalytics.logEvent()` directly, with no envelope, no schema, no identity model, and no cross-app compatibility guarantee.

**What must change, concretely, before the answer becomes "yes":**

1. Build one pilot platform adapter — Kotlin/Android is the natural starting point, informed directly by this reference app.
2. Turn `errors.md`'s malformed-payload rules into an actual, runnable, per-language validator (currently they exist only as prose plus a spec-file linter).
3. Generalize `AdTelemetry`'s `Reporter` pattern into a proper provider-adapter interface covering the full envelope, and build one concrete Firebase provider adapter against it.
4. Add a short Metrics cookbook to `docs/implementation-guide.md`, using this reference app's `AdRevenueAnalytics`/`AdTelemetry` as the worked example, so the next platform team doesn't have to rediscover the AdMob-vs-AdX double-counting nuance from scratch.
5. Explicitly own screen-detection at the adapter layer instead of leaning on a provider's automatic screen tracking, which this analysis shows does not satisfy `screen-tracking.md`.

None of this requires touching `specification/`, `events/*.yaml`, `metrics/*.yaml`, or `schema/*.yaml`. The contract is ready to be implemented; the module, in the sense of something an app can actually depend on, is not — yet.
