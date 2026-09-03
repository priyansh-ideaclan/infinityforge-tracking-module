# Repository & Adapter Architecture Decision

## Question being decided

Where should platform adapter code (Kotlin/Android, Swift/iOS, React Native) that
implements the InfinityForge Tracking contract live? Three options were on the table:

- **Option A** — everything inside `infinityforge-tracking-module`, with
  `android/`, `react-native/`, `ios/` subfolders.
- **Option B** — separate, dedicated adapter repos:
  `infinityforge-tracking-module` (contract) + `infinityforge-android-tracking` +
  `infinityforge-rn-tracking` + `infinityforge-swift-tracking`.
- **Option C** — adapter code lives inside each platform's own **App Factory
  template repository** (`native-android-app-factory`, `app-factory-rn`,
  `Swift-Project-Foundation`), each validated by its own dedicated **test/consumer
  app** (`infinityforge-tracking-test-android`, `infinityforge-tracking-test-rn`,
  `infinityforge-tracking-test-swift`), with the contract staying centralized and
  authoritative in `infinityforge-tracking-module`.

## Decision: Option C

This is not a preference — it is what this workspace already had in place before this
task began. `infinityforge-tracking-test-rn`'s and `infinityforge-tracking-test-swift`'s
own docs describe a completed port of their adapters into `app-factory-rn` and
`Swift-Project-Foundation` respectively, and this task ported the Kotlin adapter from
`infinityforge-tracking-test-android` into `native-android-app-factory` the same way
(see the top-level implementation report, section 4). Rather than discard that working
structure in favor of Option A or B, this document evaluates it honestly against the
alternatives and records why it is the right structure, not just the existing one.

## Why not Option A (everything in the contract repo)

`infinityforge-tracking-module` is explicitly, deliberately code-free —
`CONTRIBUTING.md` states plainly: "Platform-specific implementation code never belongs
in this repository, regardless of how small. It belongs in the relevant app template or
a future dedicated SDK repository." Putting Kotlin/Swift/TypeScript source inside it
would mean:

- **Dependency management collision.** The contract repo has no build system today (no
  Gradle, no CocoaPods/SPM, no npm) and versions independently of any of the three
  platforms' own dependency graphs (Kotlin/AGP/Gradle versions, CocoaPods/SPM/Swift
  toolchain versions, npm/Expo/React Native versions). Embedding three unrelated build
  systems in one repo means every platform's CI would need to run on every commit to
  the contract, even a docs-only change.
- **Release/versioning coupling.** The contract has its own semver
  (`specification/versioning.md`) independent of any adapter's release cadence. A
  Kotlin-only bugfix would force a decision about whether to bump the contract's
  version too, muddying what a version bump means.
- **Template integration friction.** Each App Factory template's own tooling
  (`scripts/configure_app.py`, `MODULES.yaml`) already assumes its own modules live in
  its own repo, at paths relative to that repo's root. Vendoring the adapter elsewhere
  would mean either a git submodule (friction every App Factory contributor already
  avoids elsewhere in this workspace) or a copy step maintained by hand.

## Why not Option B (one dedicated adapter repo per platform)

A dedicated `infinityforge-android-tracking` repo (and Swift/RN equivalents) was a
reasonable design to consider, and is closer to how a public, externally-consumed SDK
would typically be shipped (a single-purpose library repo, published to Maven
Central / CocoaPods / npm). It was rejected here for reasons specific to how this
workspace's App Factory model actually works, not because it is a bad pattern in
general:

- **The App Factory model isn't "add a library dependency," it's "clone a template."**
  `native-android-app-factory`/`app-factory-rn`/`Swift-Project-Foundation` are
  templates a new app is *cloned from* (`scripts/configure_app.py` rewrites identity,
  strips/enables capability modules) — not a set of dependencies a project declares in
  a manifest. A separately versioned, separately published `infinityforge-android-
  tracking` artifact would need real publishing infrastructure (a Maven repository, a
  release pipeline, dependency-version pinning per app) that does not exist anywhere
  else in this workspace's App Factory model — every other capability
  (`core-analytics`, `ads-admob`, `purchases-revenuecat`, `core-navigation`, etc.) is a
  source module living directly in the template, not an external package. Introducing
  exactly one capability (`core-tracking`) as an external package would be
  inconsistent with every other module boundary this factory already establishes
  (`ARCHITECTURE.md`'s module graph).
- **Extra repos to keep in lockstep for no current benefit.** A separate adapter repo
  only pays for itself when something other than "one App Factory template" consumes
  it — for example, multiple unrelated Android codebases sharing one published
  library. Today, exactly one Android codebase (`native-android-app-factory`, and apps
  cloned from it) consumes the Kotlin adapter. The same is true for RN and Swift. Until
  a second, independent consumer exists per platform, a dedicated repo adds versioning
  and publishing overhead — a release step, a version bump, a changelog, a consumer
  update — with no consumer that couldn't just as easily get the change via the
  template.
- **It would still need a validation/test app.** Even under Option B, a standalone
  adapter repo needs *something* that exercises it against a real app shell and a real
  Firebase project to be trustworthy — which is exactly what
  `infinityforge-tracking-test-android/-rn/-swift` already are. Option B would mean
  those repos additionally depend on the new adapter repos (another moving part)
  rather than containing the adapter directly, for no corresponding benefit today.

## What Option C gets right, precisely

- **The contract stays centralized and authoritative**, exactly as required. Nothing
  in `infinityforge-tracking-module` changed to accommodate any platform's
  implementation quirks; each adapter conforms to it, not the reverse (see the
  companion implementation report's section 3, "Contract changes").
- **Each platform's adapter lives where its own build/release/versioning tooling
  already operates** — `core-tracking` in `native-android-app-factory` is versioned,
  built, and tested exactly like `core-analytics`, `core-navigation`, or any other
  `core-*` module; the same is true of the RN and Swift equivalents in their own
  factories. No new tooling, publishing pipeline, or repo-management convention had to
  be invented.
- **Each platform gets a dedicated proving ground** —
  `infinityforge-tracking-test-android/-rn/-swift` — that is a *real, clonable app*
  (not a synthetic test harness), so validation happens against the same
  `configure_app.py`-driven flow a real product team would use, with a real Firebase
  project attachable. This is a stronger validation story than a library repo's unit
  tests alone would provide, because it also exercises DI wiring, lifecycle
  integration, and the App Factory's own module-boundary conventions.
- **Governance is unambiguous.** A contract change is a pull request against
  `infinityforge-tracking-module`, reviewed per its own `CONTRIBUTING.md`. An adapter
  change is a pull request against that platform's App Factory template, reviewed per
  that template's own `AGENTS.md`/`CLAUDE.md`. There is no repo where "which rules
  apply" is ambiguous.

## Trade-offs accepted

- **No single published SDK artifact.** A team outside this workspace cannot `npm
  install`/`implementation(...)` the InfinityForge Tracking Kotlin adapter as an
  isolated library — they would need to clone (or otherwise obtain) the relevant App
  Factory template. This is acceptable because the App Factory model's entire premise
  is "clone the template," not "add a dependency to an existing app" — this matches
  every other capability module, not just tracking.
- **Cross-platform drift is a discipline problem, not a tooling-enforced one.** Because
  the three adapters live in three separate repos with no shared build graph, nothing
  *mechanically* prevents the Kotlin, Swift, and RN implementations from drifting
  apart in behavior (only in source, which is expected — see the contract's own
  "one contract, many implementations" principle). Today, this is mitigated by: (a)
  the Swift adapter's own `InfinityForgeContractParityTests`, which compares a decoded
  contract snapshot against its catalogs; (b) each adapter's catalogs being hand-
  derived from the same `events/*.yaml`/`metrics/*.yaml` files, which are easy to diff
  side-by-side since all three source repos are checked out in the same workspace. If
  this workspace ever needs stronger, automated cross-adapter drift detection, the
  natural next step is a small conformance-vector file in `infinityforge-tracking-module`
  itself (canonical event/metric names, types, and required fields, in one
  machine-readable format each adapter's test suite loads and asserts against) — this
  does not require moving any adapter code, only adding one more artifact to the
  contract repo, which is squarely within what `infinityforge-tracking-module` already
  does (`schema/*.yaml` already serves an analogous purpose for the contract's own
  authoring-time checks).
- **A future public SDK is not precluded, but not built prematurely.** If InfinityForge
  Tracking is ever consumed by a codebase outside this workspace's own App Factory
  templates, Option B (or a real published package) becomes the right call at that
  point — this decision is about today's one-factory-per-platform reality, not a
  permanent architectural ceiling.

## Revisit triggers

Reconsider this decision if any of the following becomes true:

1. A second, independent Android/RN/iOS codebase (outside its App Factory template)
   needs the tracking adapter — at that point, extracting to Option B for that
   platform is the right move.
2. The three adapters' behavior drifts detectably and repeatedly despite the mitigation
   above — at that point, invest in the conformance-vector file described above before
   reaching for a repo restructure.
3. The App Factory model itself changes from "clone a template" to "install a
   published package" for other capabilities — if that happens workspace-wide, tracking
   should follow the same pattern as everything else, not lead it.
