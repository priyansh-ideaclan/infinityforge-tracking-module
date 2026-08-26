# Identity Model

This document defines how InfinityForge tracking represents "who" an event belongs to, independent of any specific identity provider or authentication system.

## The two identifiers

| Identifier | Set by | Lifetime |
|---|---|---|
| `anonymous_id` | SDK, automatically | Persists for the life of the app install, until `reset` |
| `user_id` | Application, via `identify` | Present only while a known identity is bound; cleared by `reset` |

Every event carries `anonymous_id`. `user_id` is present only once `identify` has been called and not yet cleared by `reset`.

## Lifecycle

```
Anonymous user
    |
    v
anonymous_id                      (established by `initialize`)
    |
    v
User signs in
    |
    v
user_id                            (established by `identify`)
    |
    v
Application events associated with authenticated identity
    (both anonymous_id and user_id present, linking the two)
    |
    v
Logout / reset
    |
    v
New anonymous identity           (`user_id` cleared, new anonymous_id issued)
```

## Anonymous state

Before `identify` has ever been called (or after `reset`), the session is anonymous. `initialize` ensures an `anonymous_id` exists — generated fresh on first launch and persisted for the life of the install. Events recorded in this state carry `anonymous_id` and no `user_id`.

## identify behavior

Calling `identify(user_id)`:

- sets `user_id` as the active identity for the session
- does **not** discard `anonymous_id` — both are present on subsequent events, so that the pre-login and post-login activity of the same install can be linked
- calling it again with the **same** `user_id` reaffirms the identity and has no further effect
- calling it with a **different** `user_id` than the one currently active, without an intervening `reset`, is a misuse of the contract — applications must call `reset` first (see Account switching, below)

## setUserProperties behavior

`setUserProperties` attaches persistent attributes to whichever identity is currently active (anonymous or authenticated). These attributes persist across events and app sessions until changed or cleared by `reset`. They are distinct from event properties: they describe the *user*, not a single occurrence.

## reset behavior

`reset`:

- clears the active `user_id`
- clears any properties set via `setUserProperties`
- establishes a **new** `anonymous_id` — the old one is not reused

Establishing a new `anonymous_id` on `reset`, rather than reverting to the previous anonymous identity, is a deliberate privacy choice: it prevents the next anonymous session on a shared or reused device from being associated with the previous user's anonymous activity trail. See `privacy.md`.

## Anonymous → authenticated transition

The transition happens the moment `identify` is first called in a session. Before that call, events are anonymous-only. After it, events carry both identifiers, which is what allows a backend to later resolve that a given `user_id`'s activity began during an earlier anonymous session on the same install.

## Logout semantics

A logout is a `reset` call. It must clear `user_id` and user-level properties and establish a new anonymous identity. An application must not continue sending events under the old `user_id` after logout.

## Account switching semantics

Switching from one known account to another (without an intervening logout in the UI, but a different account nonetheless) must be modeled as:

1. `reset` (clears the first account's identity)
2. `identify(new_user_id)` (establishes the second account's identity)

Calling `identify` directly with a new `user_id` while a different `user_id` is already active, without a `reset` in between, is not well-defined by this contract and must not be relied upon to cleanly separate the two identities. Implementations should treat it defensively (for example, by logging a development diagnostic), but the correctness burden is on the calling application to sequence `reset` then `identify`.
