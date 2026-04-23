# ADR 0004 — Audit trail in Firestore for MVP; migrate to Cloud Logging for production

**Status:** Accepted (with a planned migration)
**Date:** 2026-04-23
**Design doc reference:** §8.1 `audit_trail/` collection, §14.3 immutability

## Context

The design doc §8.1 stores the audit trail in a Firestore `audit_trail/`
collection. This is fine for the 4-week MVP. For production, several issues
become relevant:

1. **Schema flexibility.** Each audit event has a `details: map` of variable
   shape (remediation event, sign-off event, schema confirmation all differ).
   Firestore cannot index variable-shape maps usefully; a UI that wants to
   filter by "events where accuracy_impact < -0.05" will do full-collection
   scans.
2. **Retention.** Design doc §14.2 requires 24-month minimum retention for
   audit events. Firestore has no native time-based retention; we would
   implement archive-and-delete jobs.
3. **Immutability.** The design requires append-only. Firestore security
   rules can enforce this, but Cloud Logging is immutable by design.
4. **Cost at scale.** 24 months × thousands of audits × N events per audit
   is a lot of Firestore reads on the audit-trail UI. Cloud Logging scales
   better and is cheaper per event.

## Decision

- **MVP:** write to Firestore `audit_trail/` per design doc §8.1. Rules are
  append-only for all roles. This keeps the MVP simple and matches the doc.
- **Failure mode:** wrap the business write and the audit write in a single
  Firestore transaction. If either fails, both fail. This guarantees we
  never have a business state change without a corresponding audit event.
- **Production migration (post-MVP):**
  1. `AuditSink` protocol stays unchanged.
  2. Introduce `CloudLoggingAuditSink(AuditSink)` alongside
     `FirestoreAuditSink(AuditSink)`.
  3. Keep a minimal Firestore `audit_trail_index/` collection with
     `{trailId, auditId, action, timestamp, userId}` for fast UI listing.
  4. Flip `app.dependency_overrides` to the Cloud Logging sink.
- **Outbox pattern** (enqueue audit event in sibling collection within the
  business transaction; background task drains to the final audit store) is
  **deferred** — our MVP transaction approach is sufficient until we have
  real concurrent write traffic.

## Consequences

**Positive**
- MVP ships on schedule, matches design doc, works with Firebase emulators.
- The migration is a single-day operation post-MVP because the sink is a
  protocol.

**Negative**
- Audit-trail UI (screen S13, already cut from MVP) will be slow on large
  collections until we migrate.
- Cloud Logging migration requires GCP project changes that are not
  available during the 4-week competition window.
