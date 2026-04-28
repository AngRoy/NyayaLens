# NyayaLens — Demo Script (≈ 2 minutes)

A click-by-click walkthrough of the seeded synthetic-data demo, with
talking points the presenter can paraphrase. The whole thing should
land in two minutes; trim ruthlessly if running long.

## Pre-flight (do this once before the demo)

1. Backend up at `http://localhost:8000` (or the deployed Cloud Run URL).
2. Frontend up at `http://localhost:5173` / `https://nyayalens.web.app`.
3. The seeded CSV lives at `shared/sample_data/placement_synthetic.csv`
   (regenerate deterministically with
   `python backend/scripts/generate_synthetic_data.py --seed 42`).
4. If you've used the app before, refresh to clear the in-memory state.

## Beat-by-beat

| Time | Screen | Action | Talking point |
|---:|---|---|---|
| 0:00 | Landing | Click **Start audit demo**. | "NyayaLens is an AI accountability operating system for hiring decisions. Let me show you the full Measure → Mitigate → Govern → Recourse loop on a placement dataset that we've deliberately seeded with a known disparity." |
| 0:10 | Upload | Drop `placement_synthetic.csv`. | "600 records, fourteen columns including names, emails, roll numbers — the kind of data an Indian campus placement office actually has." |
| 0:20 | Upload response | Point at the **quality** chip showing missing-cell %, duplicate-row %, and the row-count warning if any. | "Before we touch fairness metrics, NyayaLens scores the data itself. If the dataset is too small for statistical significance we say so up front." |
| 0:30 | Schema review | Confirm Gemini's detection. | "Gemini identified Gender and Category (caste reservation) as sensitive, Placed as the outcome, Score as a continuous probability. PII columns — Name, Email, Roll_No — never reached the LLM. The PrivacyFilter strips them at the type boundary." |
| 0:45 | Dashboard | Heatmap renders. | "Five fairness metrics across the two sensitive attributes. DIR for Gender is **0.49** — that means women are placed at roughly half the rate of men with comparable academic profiles. The EEOC 80% rule line is at 0.80, so this is well over." |
| 1:00 | Conflicts panel | Show DP-vs-EO tradeoff. | "DIR and Equal Opportunity Difference disagree on this dataset — improving DIR will likely worsen EOD. NyayaLens makes the conflict explicit and asks a named human to choose." |
| 1:15 | Remediation | Click **Apply reweighting**. | "Kamiran-Calders 2012 — assigns instance weights so each (group, outcome) cell has equal probability. The before/after card shows DIR jumping to 1.00 with an estimated accuracy delta surfaced for transparency." |
| 1:30 | Sign-off | Type a one-liner. Click **Sign off**. | "Sign-off freezes the audit. Even admins cannot retroactively edit a signed audit; if a correction is needed it has to be a new audit_trail event explaining why. The Firestore rule and the API both enforce this." |
| 1:40 | Report | Click **Generate audit report**. PDF opens. | "Three sections: Part A real-data findings, Part B probe findings if we'd run an LLM bias probe, Part C the full governance record — who saw what, when, and the recourse summary the organisation can share with affected applicants." |
| 1:55 | Wrap | Brief mention of recourse + LLM Probe. | "If an applicant disputes a decision, the recourse workflow ties their request to this audit and routes it through a named reviewer. And the LLM Bias Probe runs in a separate Probe Mode — the system enforces that real-data audits and synthetic-LLM probes never mix." |

## Risk tolerance

- **If Gemini is rate-limited or down:** the explanation regenerates once, then falls back to a deterministic template. The demo path still completes.
- **If the dataset is renamed:** schema detection has a local heuristic fallback; you'll still see Gender/Category flagged even without the LLM.
- **If the network drops mid-demo:** the entire backend runs in-memory; there's no DB to lose. Just refresh and re-run the upload.

## What NOT to claim

- We never declare a system "fair" or "unfair." Findings are evidence to investigate.
- The reweighting result is *simulated on the input data*. In production the weights are fed back to a downstream scoring model — that part is post-MVP.
- Real institutional disparities are messier than the seeded fixture; the seed exists for demo reliability only.
