# ADR 0001 — Modular monolith with future-ready service extraction

**Status:** Accepted
**Date:** 2026-04-23
**Design doc reference:** §7 System Architecture

## Context

NyayaLens has seven internal services (Schema, Bias, Explain, Mitigate, Govern,
Recourse, LLM Probe, Report) but a 4-week build budget and a 3-dev team.
Microservices would multiply operational surface area (deployment, service
mesh, inter-service auth, distributed tracing) without adding user value in
the MVP window.

## Decision

- Deploy as a single FastAPI application on Cloud Run ("modular monolith").
- Enforce **strong internal service boundaries in code**: each service has
  its own package under `backend/nyayalens/core/`, its own data contracts
  (Pydantic), and communicates via explicit function calls — never via
  direct state sharing.
- Async workloads (PDF generation, large-batch analysis) are architected as
  pure functions. In MVP they run in-process via `asyncio.create_task`.
- Dependency direction is strict: `api/ → core/ → core/_contracts/ ← adapters/`.
  `core/` has no knowledge of Firebase, Gemini, or HTTP. A CI test
  (`backend/tests/contract/test_import_graph.py`) enforces this.

## Consequences

**Positive**
- Single `docker build`, single deploy, single set of secrets.
- Fast local dev loop — one `uvicorn` process.
- Extraction to separate services is mechanical when needed: each `core/*`
  package already exposes a clean interface.

**Negative**
- A single runaway request can degrade unrelated endpoints until we add
  per-endpoint CPU quotas (deferred; Cloud Run per-request concurrency limits
  give us some baseline protection).
- Scale-to-zero cold starts affect all endpoints uniformly.

## Extraction triggers (post-MVP)

Promote a `core/` module to its own service when any of these hold:
- PDF generation latency exceeds 20 s, OR
- LLM probing becomes a scheduled batch job, OR
- A single customer's data volume pushes memory beyond Cloud Run's 8 GiB cap.
