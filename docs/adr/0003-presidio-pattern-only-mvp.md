# ADR 0003 — Presidio as runtime dependency; pattern-only recognizers for MVP

**Status:** Accepted
**Date:** 2026-04-23
**Design doc reference:** §14.2 Privacy Architecture

## Context

The PII Pre-Scrubber must run before any column metadata reaches Gemini.
Building PII detection from scratch — especially for Indian identifiers like
Aadhaar (12-digit + Verhoeff checksum), PAN (mod-10 validation), GSTIN,
Voter ID — is a significant effort that Microsoft Presidio (MIT-licensed)
has already done well.

Presidio offers three detector families:
1. **Pattern-based** (`PatternRecognizer`) — regex + optional validation
   function. Fast. No model load. ~1 ms per cell.
2. **NLP-based** (`SpacyRecognizer`, `TransformersRecognizer`) — loads
   spaCy or transformer models to find PERSON, ORG, GPE entities. The
   smallest useful spaCy model (`en_core_web_sm`) is ~50 MB on disk and
   ~200 MB in memory; startup cost on Cloud Run cold start is 5-20 s.
3. **Context enhancement** — boosts confidence when contextual keywords
   appear near a match.

## Decision

- Add `presidio-analyzer` as a direct runtime dependency in
  `backend/pyproject.toml`.
- **MVP uses pattern-based recognizers only.** Import Presidio's
  `EmailRecognizer`, `PhoneRecognizer`, `CreditCardRecognizer`,
  `IpAddressRecognizer`, `UrlRecognizer`, and the India-specific
  `InAadhaarRecognizer`, `InPanRecognizer`, `InGstinRecognizer`,
  `InPassportRecognizer`, `InVoterRecognizer`,
  `InVehicleRegistrationRecognizer`.
- Add one custom `IndianRollNoRecognizer` (regex approximating Indian college
  roll numbers such as `21CS001`, `20ECE042`).
- **Column-level detection** is built on top of per-cell pattern results:
  if >70% of non-null cells in a column match any PII entity type, the
  entire column is treated as PII.
- spaCy NER (`SpacyRecognizer`) is **deferred to post-MVP**. It adds
  5-20 s to Cloud Run cold start and breaks our schema-detection SLA
  (<5 s per design §15.1).

## Consequences

**Positive**
- Instant cold start. Schema detection stays within the <5 s budget.
- Indian-specific PII coverage out of the box.
- Zero spaCy model download; Docker image stays small.

**Negative**
- Free-text fields with embedded names ("John called me yesterday about
  the role") will not be flagged. Mitigation: we require a column-level
  heuristic (high-cardinality string columns with >80% unique values are
  flagged as likely identifiers, even without an entity match).
- Post-MVP work is required to add spaCy NER for free-text columns
  (remarks, interview notes). A follow-up ADR will cover it.

## Reference file paths

- `Y:\SolutionChallenge\presidio\presidio-analyzer\presidio_analyzer\pattern_recognizer.py`
- `Y:\SolutionChallenge\presidio\presidio-analyzer\presidio_analyzer\predefined_recognizers\country_specific\india\`
- `Y:\SolutionChallenge\presidio\presidio-analyzer\presidio_analyzer\recognizer_registry\recognizer_registry.py`
