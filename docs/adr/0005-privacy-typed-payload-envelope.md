# ADR 0005 — Privacy enforced as a type, not a convention

**Status:** Accepted
**Date:** 2026-04-23
**Design doc reference:** §14.2 Privacy Architecture; Privacy Modes table

## Context

NyayaLens must never leak raw PII (names, emails, phones, Aadhaar numbers) to
the Gemini API. The design doc defines three privacy modes (Strict, Balanced,
Local) and specifies what classes of data may reach the model in each.

The most dangerous failure is a well-meaning developer adding a new Gemini
call path and forgetting to invoke the PII Pre-Scrubber. With a decorator or
a service-level convention, this mistake is invisible at review time and
catastrophic at runtime.

## Decision

Privacy is enforced **at the type boundary**, not by convention.

1. `core/_contracts/llm.py` defines `LLMPayload` as a discriminated union of
   `StrictPayload`, `BalancedPayload`, and `LocalPayload`. Each is a frozen
   Pydantic model whose fields correspond to the design-doc "LLM Payload
   Contract" table (column names, dtypes, distribution summaries, redacted
   samples — never raw rows).
2. `LLMClient.generate_structured` and `LLMClient.generate_text` accept
   **only** `LLMPayload`. They do not accept `str`.
3. `PrivacyFilter` in `core/schema/pii.py` is the **sole constructor** of
   `LLMPayload` instances. It receives raw dataframes and returns an
   `LLMPayload` after applying column-level PII scrubbing.
4. `GeminiAdapter` — the concrete `LLMClient` — emits a `PrivacyLogEntry` to
   the audit sink on every call, recording which columns were inspected,
   what PII was detected, what masking was applied, and which payload class
   was sent.

With this design:

- Passing a raw string to the adapter is a `mypy` error, caught in CI before
  merge.
- Adding a new call site requires constructing an `LLMPayload`, which
  requires using the `PrivacyFilter`, which applies the scrubber.
- The `PrivacyLogEntry` gives us an auditable record per call — privacy
  becomes a mechanism, not a claim.

## Consequences

**Positive**
- Single, non-bypassable chokepoint for all LLM traffic.
- New contributors cannot accidentally leak PII without fighting the type
  system.
- Privacy logging is automatic and uniform.

**Negative**
- More boilerplate for simple Gemini calls (must construct an envelope
  even for operations with no PII risk, e.g. probe-mode synthetic content).
  Mitigation: `LLMPayload.no_user_data()` class method for calls that have
  no user-supplied content.
- If `mypy` is not enforced in CI, the guarantee degrades. Mitigation:
  `mypy --strict` is part of the backend CI job (see
  `.github/workflows/backend-ci.yml`).
