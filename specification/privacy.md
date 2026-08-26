# Privacy Rules

These rules are platform-independent and apply to every event, every property, and every user-level attribute set through this contract, regardless of which adapter or analytics provider ultimately receives the data.

## Prohibited data categories

The following must **never** appear in an event property, a user property, an event name, a screen name, or any other value passed through this contract:

- passwords, passphrases, or password hints
- authentication tokens, session tokens, refresh tokens, or API keys
- payment card data (card numbers, CVV/CVC, expiry, or any other PAN-adjacent data)
- private keys, cryptographic secrets, or credentials of any kind
- unnecessary sensitive personal information — including but not limited to government-issued identification numbers, precise home addresses, health information, or other data not clearly required for the event's documented purpose

This list is a floor, not a ceiling. When in doubt about whether a value is sensitive, do not track it.

## General principle

Event and user properties should describe **behavior and state**, not **identity or sensitive content**. A property should answer "what happened" or "what is true about this user's configuration or cohort," not carry free-form personal content. Prefer stable identifiers, categories, and enums over raw personal data — for example, a `plan` property identifying a subscription tier is appropriate; a property containing a user's full name or email address is not.

## Review and approval for exceptional data

If a genuinely justified need arises to collect something that could be considered sensitive personal information, it must go through explicit review and be documented as an approved exception in this repository (via the change process in `CONTRIBUTING.md`) **before** any implementation collects it. The default is that such data is not collected; an undocumented exception is not a valid exception, regardless of the application's own justification.

## Scope of these rules

These rules apply equally to canonical events (`events/*.yaml`) and to app-specific events and properties that applications add on top of this contract. Being outside the canonical taxonomy does not exempt a property from these rules.

## What this document does not claim

This document defines InfinityForge's own internal data-minimization rules. It does not, by itself, constitute or guarantee compliance with any specific privacy law or regulation (such as GDPR, CCPA, or others) in any jurisdiction. Teams building on this contract remain responsible for determining and meeting their own regulatory obligations; following these rules is necessary but not automatically sufficient for that purpose.
