# NyayaLens

> **न्यायलेन्स** — *The Eye of Justice*
> An AI accountability operating system for automated hiring decisions.
> Built for Solution Challenge 2026: Build with AI.

NyayaLens helps organizations **measure** fairness in hiring AI, **mitigate**
disparities with human approval, **govern** every decision with an immutable
audit trail, and **support recourse** for affected applicants.

Stack: Flutter web · FastAPI · Firebase · Cloud Run · Gemini API.
License: Apache 2.0 (see `LICENSE` and `NOTICE`).

---

## Four-Layer Accountability Stack

| Layer | Function | What NyayaLens does |
|---|---|---|
| **1 — Measure** | Detect | Gemini-powered schema understanding, 5 fairness metrics, intersectional views, LLM bias probing, conflict detection |
| **2 — Mitigate** | Intervene | Reweighting, proxy-feature detection, LLM prompt hardening, before/after simulation — **always with human approval** |
| **3 — Govern** | Accountability | Policy config, role-based access, sign-off workflow, immutable audit trail, regulatory mapping |
| **4 — Recourse** | Justice | Applicant-facing explanations, appeal workflow, institutional loop closure |

See `docs/system-design.md` for the full design (problem framing, competitive
landscape, feature catalog, wireframes, regulatory alignment, and roadmap).

---

## Repository layout

```
NyayaLens/
├── backend/        FastAPI service — metrics engine, Gemini adapter, PDF generator
├── frontend/       Flutter web client — 13 screens from Upload through Recourse
├── shared/         JSON schemas, sample data, Firestore rules
├── infra/          Firebase + Cloud Run deployment config
├── docs/           System design doc + architecture decision records (ADRs)
└── .github/        CI workflows
```

Key architectural rules:

- `backend/nyayalens/core/` is **domain-agnostic**. It must not import Firebase,
  Gemini, or FastAPI. A CI test (`test_import_graph.py`) enforces this.
- `backend/nyayalens/adapters/` is the only layer that imports external SDKs.
- **Privacy is a type, not a convention.** The Gemini adapter accepts only
  `LLMPayload` envelopes produced by the `PrivacyFilter`. Raw strings are
  a compile-time error.

---

## Getting started (local dev)

### Prerequisites

- Python 3.11+
- Flutter SDK 3.x (Dart 3) — install from https://flutter.dev
- Firebase CLI 13.x — `npm install -g firebase-tools`
- A Gemini API key — set `GEMINI_API_KEY` in `backend/.env`

### Backend

```sh
cd backend
python -m venv .venv
. .venv/bin/activate        # Windows bash: source .venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env        # then fill GEMINI_API_KEY
pytest                       # unit tests should pass immediately
uvicorn nyayalens.main:app --reload --port 8000
```

### Firebase emulators

From repo root:

```sh
firebase emulators:start --only auth,firestore,storage
```

The backend auto-detects `FIRESTORE_EMULATOR_HOST` and `FIREBASE_AUTH_EMULATOR_HOST`
environment variables.

### Frontend

```sh
cd frontend
flutter pub get
flutter run -d chrome
```

### Full-stack dev loop

From repo root, with all three running in separate terminals:

1. `firebase emulators:start`
2. `cd backend && uvicorn nyayalens.main:app --reload`
3. `cd frontend && flutter run -d chrome`

---

## Demo dataset

`shared/sample_data/placement_synthetic.csv` is seeded with a known 3:1
demographic disparity. It is regenerated deterministically with:

```sh
python backend/scripts/generate_synthetic_data.py --seed 42
```

The expected demo path produces **DIR = 0.56** before reweighting and
**DIR ≈ 0.84** after — the headline before/after moment.

Real hiring data is never committed. `placement_real_anchor.csv` is in
`.gitignore`.

---

## Evidence modes

NyayaLens strictly separates two modes — they are never intermixed in UI,
reports, or data:

- **Audit Mode** — analyzes real, public, or org-approved datasets.
- **Probe Mode** — uses Gemini/Gemma to generate synthetic scenarios and
  tests the LLM's own bias when evaluating them.

Every audit record carries a `mode` field; the top-bar badge in the UI
displays data provenance (`Real` / `Benchmark` / `Synthetic` / `LLM-Generated`).

---

## Attribution

NyayaLens studies battle-tested OSS tools without wrapping them. See `NOTICE`
for full attribution to IBM AI Fairness 360, Microsoft Fairlearn, UChicago
Aequitas, Microsoft Presidio, Holistic AI, Oracle Guardian AI, Google PAIR
What-If Tool / LIT, and Microsoft Responsible AI Toolbox.

---

## Status

Week 1 — Foundation. This README and the scaffold are the first artifacts.
See `docs/adr/` for architectural decisions and the plan tracker for the
4-week sprint.

— *Team Zenith*
