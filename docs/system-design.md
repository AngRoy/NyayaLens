# NyayaLens — System Design Document
## The Eye of Justice | AI Accountability Operating System
### Solution Challenge 2026: Build with AI

**Document version:** 5.0 (Final)
**Last updated:** April 23, 2026
**Classification:** Technical System Design — Production-Ready

---

## Table of Contents

1. Executive Summary
2. Problem Statement & Market Opportunity
3. Competitive Landscape & Differentiation
4. Unique Selling Proposition (USP)
5. Product Philosophy & Sociotechnical Design Principles
6. Feature Catalog
7. System Architecture
8. Data Architecture & Schema Design
9. API Design & Contracts
10. Process Flow Diagrams
11. Use Case Diagrams
12. Wireframe Specifications
13. Technology Stack & Justification
14. Security, Privacy & Compliance
15. Scalability & Performance Engineering
16. Estimated Implementation Cost
17. Development Timeline & Sprint Plan
18. Regulatory Alignment Matrix
19. Future Roadmap
20. Appendices

---

## 1. Executive Summary

**NyayaLens** (Sanskrit: न्यायलेन्स — "The Eye of Justice/Logic") is an AI accountability operating system — a control plane that helps institutions measure disparities, test mitigations, document tradeoffs, assign responsibility, and manage recourse in automated decision pipelines. The platform implements a four-layer accountability stack — Measure, Mitigate, Govern, Recourse — aligned with both the NIST AI Risk Management Framework and India's AI Governance Guidelines (the Seven Sutras).

**What NyayaLens is NOT:** It does not claim to automatically solve or certify fairness.

**What NyayaLens IS:** An accountability and mitigation platform that combines fairness measurement, technical intervention, governance, and recourse in a single system. It helps institutions measure disparities, test mitigations, document tradeoffs, assign responsibility, and support recourse through a guided human-in-the-loop workflow.

**The NyayaLens Stack:**

| Layer | Function | What it does |
|---|---|---|
| **Layer 1 — Measure** | Detect | Detect disparities, quantify harms, analyze metric conflicts, visualize patterns |
| **Layer 2 — Mitigate** | Intervene | Offer technical interventions for data, model behavior, and LLM outputs; simulate before/after effects |
| **Layer 3 — Govern** | Accountability | Require human approval, assign responsibility, log decisions, map to policy and regulation |
| **Layer 4 — Recourse** | Justice | Generate affected-individual explanations, support appeals, close the loop institutionally |

**Primary domain (v1.0):** AI-assisted hiring and recruitment pipelines.
**Primary user:** HR Compliance Officers, Talent Acquisition Leads, Placement Cell Coordinators.
**Architecture:** Modular monolith with asynchronous workers and future-ready service extraction. Hiring-first with extensible domain layers.

**Evidence Modes:** Audit Mode (real/public dataset analysis) and Probe Mode (LLM-generated scenario red-teaming).
**Data Strategy:** Three-tier — real privacy-safe anchor data, public benchmarks, synthetic stress-test sets.
**Model Backends:** Gemini API (core, hosted inference) and Gemma 4 (optional, privacy-preserving local deployments).
**Core Google Technologies:** Flutter (web-first MVP, mobile follow-on), Firebase Auth + Firestore + Cloud Storage (data layer), Cloud Run (compute), Gemini API (intelligence), Cloud Functions (async processing).
**Strategic Google Technology:** Gemma 4 (optional open-weight backend for privacy-sensitive deployments and Probe Mode).

---

## 2. Problem Statement & Market Opportunity

### 2.1 The Problem

Automated decision systems now influence who gets hired, who gets loans, who receives healthcare, and who gets admitted to universities. These systems are trained on historical data that reflects decades of systemic discrimination. When an AI learns from biased data, it doesn't just replicate bias — it scales it, automates it, and hides it behind a veneer of algorithmic objectivity.

**The critical gap is not detection alone — it's the full lifecycle from detection through mitigation to accountability.**

Tools exist to measure bias (AIF360, Fairlearn, Aequitas) and some offer algorithmic mitigation. But the full lifecycle — from measurement through controlled mitigation to institutional governance and individual recourse — is not addressed by any single accessible tool. NyayaLens operationalizes fairness measurement by embedding it inside an accountability system that also supports mitigation, governance, sign-off, and recourse.

The hard problems that remain unsolved are:

- **Who is responsible** when an algorithm discriminates?
- **Who decides** which tradeoff is acceptable?
- **What happens** when an affected individual challenges a decision?
- **Where is the documentation** proving the organization considered fairness?
- **How does a non-technical decision-maker** engage with fairness analysis without a data science team?

Existing tools address parts of this lifecycle individually, but they are generally designed for technical users and do not integrate measurement, mitigation, governance, and recourse into a single guided workflow. NyayaLens fills this gap.

### 2.2 The Harm Model (Causal Chain)

```
Historical hiring data contains systemic bias
    ↓
AI screening tool trained on this data learns discriminatory patterns
    ↓
The tool systematically scores certain demographic groups lower
    ↓
Fewer members of disadvantaged groups receive interviews
    ↓
Organizational workforce becomes less diverse
    ↓
New hiring data reinforces the original bias
    ↓
Individual qualified applicants lose career opportunities
    based on group membership, not individual merit
    ↓
Without accountability mechanisms, the organization
    has no documentation, no recourse path, and no audit trail
```

### 2.3 Market Opportunity

**Regulatory pressure (immediate):**

- **EU AI Act (August 2, 2026):** AI systems used in employment are classified as "high-risk" under Annex III. Organizations must implement mandatory risk assessments, bias testing, human oversight, transparency disclosures, and continuous monitoring. Non-compliance carries fines up to €15 million or 3% of global annual turnover. This deadline is 3.5 months away.
- **India AI Governance Guidelines (February 2026):** Seven governing sutras including "Fairness & Equity" and "Accountability." Thirteen projects selected under the IndiaAI Mission's Safe & Trusted AI pillar specifically address bias mitigation, explainability, and governance testing.
- **US State Laws:** NYC Local Law 144 requires annual independent bias audits. Colorado AI Act (June 2026) requires impact assessments for high-risk systems. California regulations require 4-year record retention of automated decision data.
- **NIST AI RMF 1.0:** Govern → Map → Measure → Manage framework adopted as the global standard for AI risk management.

**Market size:**

- 83% of employers use some form of automated screening (SHRM, 2025)
- The global AI in recruitment market is projected at $890M by 2028
- Existing no-code accountability platforms for hiring fairness are either enterprise-priced ($30K+/year) or limited to measurement without governance, sign-off, or recourse workflows
- Enterprise alternatives (Fiddler, Credo AI, Arthur AI) cost $30,000–$250,000/year

**Timing:** NyayaLens arrives at the exact moment when regulations demand accountability tools but the market offers only code-first metric libraries or six-figure enterprise platforms. The gap is massive, urgent, and perfectly timed for this competition.

### 2.4 Opportunity Assessment

**a. How different is it from any existing idea?**

Existing tools in this space represent strong contributions: AIF360 provides 70+ metrics and 10+ mitigation algorithms; Fairlearn offers clean API-driven mitigation patterns; Aequitas brings policy-oriented audit framing; the What-If Tool pioneered interactive fairness exploration. However, these tools are designed for ML engineers working in code environments and generally focus on the measurement and algorithmic mitigation stages. NyayaLens builds on their foundations but extends the workflow to include guided onboarding for non-technical users, institutional governance, human-in-the-loop mitigation approval, and applicant recourse — capabilities that address the organizational and regulatory gaps emerging as AI governance regulations take effect.

NyayaLens builds on these foundations but extends the workflow beyond measurement and algorithmic mitigation into institutional governance, human accountability, and individual recourse — the layers that regulatory frameworks like the EU AI Act and India's AI Governance Sutras now demand but that existing tools do not yet address in an accessible, guided format.

**b. How will it solve the problem?**

NyayaLens operationalizes both the NIST AI RMF and a four-layer accountability stack:

| NyayaLens Layer | NIST Function | Implementation |
|---|---|---|
| **Layer 1 — Measure** | MAP + MEASURE | Gemini-powered schema detection, 5 fairness metrics, intersectional analysis, LLM bias probing, conflict detection |
| **Layer 2 — Mitigate** | MANAGE | Reweighting, representation balancing, threshold optimization, proxy-feature detection, LLM prompt hardening, candidate anonymization |
| **Layer 3 — Govern** | GOVERN | Policy configuration, risk thresholds, role-based access, human sign-off workflows, decision logging, regulatory mapping |
| **Layer 4 — Recourse** | MANAGE | Applicant-facing explanations, human review requests, appeal tracking, institutional loop closure |

**c. USP of the proposed solution**

See Section 4 for full USP. In one sentence:

> NyayaLens is a no-code AI accountability and mitigation platform that combines fairness measurement, technical intervention, governance, and recourse for automated hiring decisions — powered by Gemini, aligned with India's AI Governance Sutras and the EU AI Act, with built-in human-in-the-loop approval at every stage.

---

## 3. Competitive Landscape & Differentiation

### 3.1 Detailed Competitor Analysis

#### IBM AI Fairness 360 (AIF360)

**What it is:** Open-source Python library with 70+ fairness metrics and 10+ mitigation algorithms (pre-processing, in-processing, post-processing).

**Strengths:** Most comprehensive metric library. Academic gold standard. Battle-tested statistical implementations. Scikit-learn compatible.

**Weaknesses that NyayaLens exploits:**
- Requires Python fluency and ML expertise
- Data must be converted to proprietary BinaryLabelDataset/RegressionDataset objects
- No null value handling — manual data cleaning required
- Manual specification of protected attributes and privileged/unprivileged groups
- No web UI — purely programmatic (Jupyter notebook workflow)
- Output is raw numbers — no natural language explanations
- No governance, sign-off, or accountability workflows
- No recourse or contestability features
- Complex dependency management; version conflicts with scikit-learn common
- Only tabular data; no LLM auditing capability

**NyayaLens advantage:** Everything AIF360 requires manual Python setup for, NyayaLens automates through Gemini. Everything AIF360 doesn't do (governance, accountability, recourse), NyayaLens builds as core features.

#### Microsoft Fairlearn

**What it is:** Open-source Python package with fairness metrics (MetricFrame) and 3 mitigation algorithms (ExponentiatedGradient, GridSearch, ThresholdOptimizer).

**Strengths:** Clean API, active development (commits as recent as March 2026), good documentation, Azure ML integration, Jupyter dashboard widget.

**Weaknesses that NyayaLens exploits:**
- Only supports group fairness (not individual or counterfactual)
- Dashboard is a Jupyter widget, not a standalone application
- Requires manual sensitive feature specification
- No automated detection of protected attributes
- No natural language explanations
- Azure-centric ecosystem
- Fairlearn's own documentation explicitly states: "Fairness is a fundamentally sociotechnical challenge and cannot be solved with technical tools alone"
- No governance, accountability, or recourse features

**NyayaLens advantage:** NyayaLens takes Fairlearn's own philosophical position seriously and builds the sociotechnical layers (governance, human accountability, contestability) that Fairlearn explicitly says are needed but doesn't implement.

#### Google What-If Tool / LIT

**What it is:** Browser-based visual exploration tool for ML model behavior. Part of Google PAIR initiative. Google's own docs now recommend LIT (Learning Interpretability Tool) as the successor.

**Strengths:** No-code visual exploration, counterfactual analysis, 5 fairness metrics, interactive data point editing.

**Weaknesses that NyayaLens exploits:**
- No longer actively maintained (Google recommends LIT)
- Exploration only — no mitigation, no governance, no reporting
- No export features (screenshot only)
- No automated reporting or audit trails
- No natural language explanations
- Limited to binary classification fairness
- Requires TensorBoard or Jupyter environment

**NyayaLens advantage:** NyayaLens is a complete lifecycle tool (detect → explain → govern → remediate → document → recourse). What-If Tool is an exploration sandbox.

#### Google LLM Comparator

**What it is:** Web app for side-by-side evaluation of two LLM models' output quality. Provides win rates, rationale summaries, and quality analysis.

**Strengths:** Clean UI, comparative model evaluation, integrated with Vertex AI.

**Critical distinction:** LLM Comparator answers "which model produces better outputs?" It compares Model A vs Model B on the same prompts. It has ZERO demographic perturbation, ZERO fairness metrics, ZERO bias detection across protected attributes. It is an output quality tool, not a fairness tool.

**NyayaLens advantage:** NyayaLens's LLM Bias Probe sends identical prompts with systematically varied demographic markers and measures response disparities across groups — a distinct capability from general output quality comparison.

#### Aequitas (UChicago DSSG)

**What it is:** Bias auditing toolkit for predictive risk assessment. Python API + CLI + basic web app. Confusion matrix-based metrics with disparity calculations.

**Strengths:** Clean audit workflow, policy-oriented framing, good visualization, Pareto-optimal fairness in v1.0.

**Weaknesses that NyayaLens exploits:**
- Binary classification only
- Web app is minimal (basic upload + static plots)
- No AI-powered explanations
- No governance or accountability workflows
- No recourse features
- Limited metric coverage

**NyayaLens advantage:** Full lifecycle accountability with AI-powered explanations, governance, and recourse — not just audit.

#### Enterprise Platforms (Fiddler AI, Credo AI, Arthur AI)

**What they are:** Production ML monitoring and governance platforms with compliance documentation, drift detection, and fairness monitoring.

**Pricing:** $30,000–$250,000+/year

**NyayaLens advantage:** Free, open-source, purpose-built for organizations that can't afford enterprise governance. This is the demographic that matters most — mid-size companies, educational institutions, NGOs, and public sector organizations in India and the Global South.

### 3.2 Competitive Differentiation Matrix

| Capability | AIF360 | Fairlearn | What-If/LIT | LLM Comp. | Aequitas | Enterprise | **NyayaLens** |
|---|---|---|---|---|---|---|---|
| No-code interface | ✗ | ✗ | Partial | ✓ | Partial | ✓ | **✓** |
| Auto-detect sensitive attrs | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| AI-powered explanations | ✗ | ✗ | ✗ | ✗ | ✗ | Partial | **✓** |
| Governance workflow | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Human sign-off | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Applicant recourse | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| LLM bias probing | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Audit report generation | ✗ | ✗ | ✗ | ✗ | Partial | ✓ | **✓** |
| Before/after comparison | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Metric conflict surfacing | ✗ | ✗ | ✗ | ✗ | ✗ | Partial | **✓** |
| Mobile support | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Post-MVP |
| Regulatory mapping | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| Free / open-source | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | **✓** |
| India AI Sutras alignment | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |

In this comparison, NyayaLens covers the broadest range of capability areas. Open-source tools like AIF360 and Fairlearn are strong on measurement and algorithmic mitigation; enterprise platforms like Fiddler and Credo AI add governance and monitoring. NyayaLens's distinct contribution is combining measurement, mitigation, governance, and recourse in a single no-code workflow accessible to non-technical users, at no cost.

---

## 4. Unique Selling Proposition (USP)

### Primary USP

**NyayaLens combines fragmented fairness capabilities — measurement, mitigation, governance, and recourse — into a single guided, no-code accountability workflow.**

Existing fairness tooling is code-first, metric-focused, and generally weak on the institutional layers that follow measurement: controlled intervention, human accountability, and affected-individual recourse. NyayaLens addresses this gap with a hiring-first accountability and mitigation platform that implements the complete Measure → Mitigate → Govern → Recourse lifecycle.

### Three Differentiating Capabilities

**1. Gemini-Powered Intelligent Schema Understanding**
Upload a CSV, and Gemini identifies which columns are sensitive attributes, which is the decision outcome, and what the data context is — without manual configuration. This eliminates the most common barrier to adoption in existing fairness tools, which require users to manually specify protected attributes, privileged groups, and outcome columns in code.

**2. Four-Layer Accountability Stack**
NyayaLens implements a complete stack — not just measurement:
- **Measure** — detect disparities, quantify harms, analyze metric conflicts, visualize patterns
- **Mitigate** — offer technical interventions for data, model behavior, and LLM outputs; simulate before/after effects with human approval
- **Govern** — require human sign-off, assign accountability, log decisions, map to policy and regulation
- **Recourse** — generate affected-individual explanations, support appeals, close the loop institutionally

Some existing tools address measurement and partial mitigation (AIF360, Fairlearn); others offer enterprise governance at scale (Fiddler, Credo AI). NyayaLens's contribution is integrating all four layers into a single accessible workflow — with Gemini-powered guided onboarding, explicit human-in-the-loop mitigation, and applicant recourse — at zero cost, designed for non-technical users.

**3. LLM Bias Probe**
NyayaLens probes generative AI systems for demographic bias within institutional decision workflows — not by comparing model quality (like LLM Comparator), but by sending identical prompts with systematically varied demographic markers and measuring response disparities. This is a distinct capability from existing LLM evaluation tools, which focus on output quality rather than fairness across demographic groups.

---

## 5. Product Philosophy & Sociotechnical Design Principles

### 5.1 Core Philosophy

NyayaLens is built on the understanding that **fairness is not just a number — but it is also not just a conversation.** It is a sociotechnical challenge that requires rigorous measurement, controlled technical intervention, institutional governance, and individual recourse. NyayaLens does not claim to automatically solve or certify fairness. It detects, tests, and mitigates measurable harms. It provides controlled technical interventions and requires human accountability for deployment. It improves fairness characteristics of datasets, models, and LLM behavior — while making tradeoffs explicit.

### 5.2 Design Principles

**Principle 1: Measure Rigorously**
NyayaLens applies validated statistical fairness metrics, surfaces conflicts between them, and quantifies disparities with appropriate caveats about sample sizes, data provenance, and reference thresholds.

**Principle 2: Mitigate Carefully**
NyayaLens provides real technical interventions — reweighting, threshold optimization, proxy detection, LLM prompt hardening — but never applies them silently. Every intervention shows its before/after impact and requires human approval.

**Principle 3: Govern Explicitly**
When fairness metrics conflict (and they will — demographic parity and equalized odds often point in different directions), NyayaLens surfaces the conflict, explains each side in plain language, and requires a named human to choose and document their reasoning.

**Principle 4: Support Recourse**
Any person affected by an automated decision should have access to a clear, non-technical explanation of what factors were considered and how to request a human review. NyayaLens generates applicant-facing recourse summaries that organizations can share.

**Principle 5: Document Everything**
An organization that measured, mitigated, and documented its fairness decisions is fundamentally different from one that didn't. NyayaLens creates an immutable audit trail: who analyzed what, when, what they found, what intervention they chose, and why.

**Principle 6: Accessibility Is Justice**
If only organizations with $250,000 enterprise budgets and ML engineering teams can audit their AI systems, then accountability becomes a privilege. NyayaLens is free, open-source, and designed for a non-technical user operating alone.

### 5.3 Alignment with India AI Governance Sutras

| India AI Sutra | NyayaLens Implementation |
|---|---|
| **Trust** | Transparent metrics, grounded explanations, audit trails |
| **People-First Governance** | Applicant recourse portal, affected-individual transparency |
| **Innovation over Restraint** | Enables responsible innovation by providing accountability tools |
| **Fairness & Equity** | Core mission — detecting and investigating demographic disparities |
| **Accountability** | Human sign-off, decision documentation, named responsibility |
| **Understandability by Design** | Gemini-powered plain-language explanations of all metrics |
| **Safety, Resilience & Sustainability** | Open-source, scalable, maintainable architecture |

### 5.4 Alignment with NIST AI RMF

| NIST Function | NyayaLens Layer | Modules |
|---|---|---|
| **MAP** | Layer 1 — Measure | Schema Engine (Gemini-powered data understanding, sensitive attribute detection, decision pipeline mapping) |
| **MEASURE** | Layer 1 — Measure | Bias Engine (5 core metrics, intersectional analysis, LLM bias probing, conflict detection) |
| **MANAGE** | Layer 2 — Mitigate | Mitigation Engine (reweighting, threshold optimization, proxy detection, LLM prompt hardening, before/after simulation) |
| **GOVERN** | Layer 3 — Govern | Governance Engine (policy configuration, role assignment, threshold setting, human sign-off workflows, audit trail) |
| **MANAGE** | Layer 4 — Recourse | Recourse Engine (applicant explanations, human review requests, appeal tracking, institutional loop closure) |

### 5.5 Open-Source Foundations

NyayaLens builds on the shoulders of battle-tested open-source projects. We learn from their strengths and fill their gaps:

| Project | What we learn | What we add |
|---|---|---|
| **AIF360** (IBM) | Metric breadth, mitigation taxonomy, lifecycle framing | No-code interface, governance, recourse, LLM probing |
| **Fairlearn** (Microsoft) | Clean API design, MetricFrame decomposition, threshold optimization | Gemini explanations, human sign-off, institutional accountability |
| **Aequitas** (UChicago) | Policy-oriented audit framing, communicable reports | Full mitigation layer, governance workflows, recourse portal |
| **Responsible AI Toolbox** (Microsoft) | Integrated assessment workflows, interpretability + fairness in one surface | Domain-specific hiring workflow, Gemini intelligence, mobile support |
| **What-If Tool / LIT** (Google PAIR) | Interactive exploration, perturbation UX | Production accountability (not just exploration), human-in-the-loop mitigation |
| **Presidio** (Microsoft) | PII detection, masking, anonymization patterns | Integrated into NyayaLens PII Pre-Scrubber architecture |
| **Holistic AI** | Broader trustworthiness framing beyond pure fairness | Domain-specific accountability workflows |
| **Oracle Guardian AI** | Combines fairness/bias assessment with privacy estimation in a single framework | Privacy-aware fairness analysis patterns integrated into NyayaLens's dual privacy + fairness pipeline |
| **Guardian AI** (Oracle) | Combined fairness/bias detection with privacy estimation in a single framework | Privacy-aware fairness analysis approach; validates our dual concern for bias + data protection |

---

## 6. Feature Catalog

### 6.1 Core Features (MVP — Ships in Competition)

#### F1: Intelligent Data Ingestion
- Drag-and-drop CSV/Excel upload
- Automatic data type inference (numeric, categorical, datetime, text)
- Missing value detection and handling recommendations
- Sample size validation (minimum thresholds for statistical significance)
- Data quality scoring

#### F2: Gemini-Powered Schema Detection
- Automatic identification of sensitive/protected attributes (gender, age, race, caste, disability, religion)
- Automatic identification of outcome/decision columns (hired/not hired, approved/denied, score)
- Automatic identification of feature columns vs. identifier columns
- Confidence scores for each detection
- One-click user confirmation or override
- Support for domain-specific attribute naming conventions (Indian datasets: "Category" for caste, "Community" for religion)

#### F3: Fairness Measurement Engine
Five core metrics computed across all detected sensitive attributes:

| Metric | Formula | Interpretation | Reference Threshold |
|---|---|---|---|
| **Statistical Parity Difference (SPD)** | P(Ŷ=1\|D=unprivileged) − P(Ŷ=1\|D=privileged) | Difference in positive outcome rates | \|SPD\| < 0.1 |
| **Disparate Impact Ratio (DIR)** | P(Ŷ=1\|D=unprivileged) / P(Ŷ=1\|D=privileged) | Ratio of positive outcome rates | DIR ≥ 0.80 (EEOC 80% rule) |
| **Equal Opportunity Difference (EOD)** | TPR_unprivileged − TPR_privileged | Difference in true positive rates | \|EOD\| < 0.1 |
| **Consistency Score** | 1 − (1/n) Σ \|ŷᵢ − mean(ŷ_kNN(i))\| | How similarly similar individuals are treated | > 0.80 |
| **Calibration Difference** | \|P(Y=1\|Ŷ=p, D=0) − P(Y=1\|Ŷ=p, D=1)\| | Predicted probability accuracy across groups | < 0.05 |

Note: Only DIR ≥ 0.80 has direct legal heritage (EEOC Uniform Guidelines). Other thresholds are common engineering reference points used in fairness research, not legal standards.

Each metric is computed for:
- Each sensitive attribute independently
- Simple cross-tabulation (e.g., gender × department, age group × outcome)

#### F4: Bias Heatmap Visualization
- Interactive matrix showing metric values across all sensitive attributes
- Color-coded severity: green (within threshold), amber (borderline), red (exceeds threshold)
- Click-to-drill-down on any cell to see detailed distribution
- Animated rendering for demo impact
- Exportable as PNG/SVG

#### F5: Gemini-Powered Explanations
For each metric result, Gemini generates:
- **Plain-English summary:** "Women in this dataset are 2.8x less likely to be selected than men with equivalent qualifications."
- **What this means:** "The disparate impact ratio of 0.56 is well below the 80% threshold used in US employment law."
- **Possible root causes:** "The disparity correlates most strongly with 'years of continuous employment,' which penalizes career gaps — a known proxy for gender."
- **What to consider:** "This finding warrants investigation. Consider whether 'years of continuous employment' is a valid predictor for this role."

**Grounding protocol:** Every explanation is templated with exact metric values injected from the engine. Gemini translates numbers into language; it does not generate numbers. A disclaimer is always shown: "This is interpretive guidance to support human decision-making, not legal or ethical judgment."

#### F6: Metric Conflict Surfacing
When metrics disagree (e.g., improving demographic parity worsens equalized odds), NyayaLens:
- Highlights the conflict visually
- Explains each metric's perspective in plain language
- Shows the Pareto frontier of possible tradeoffs
- Requires the user to explicitly choose which fairness criterion to prioritize
- Records the choice and justification

#### F7: Mitigation Layer (Layer 2 of the Stack)

NyayaLens does not claim to automatically solve fairness. It provides measurable mitigation strategies for datasets, models, and LLM-assisted workflows, with human-in-the-loop approval and full auditability.

**For structured/tabular hiring data:**

| Intervention | What it does | MVP? |
|---|---|---|
| **Reweighting** | Assigns instance weights to equalize positive outcome rates across groups | ✓ MVP |
| **Proxy-feature detection** | Identifies features that correlate with sensitive attributes and may act as discrimination proxies | ✓ MVP |

**Proxy-Feature Detection — Technical Specification:**

| Element | Definition |
|---|---|
| **Trigger** | Runs automatically after schema detection identifies sensitive attributes. Computes correlation between every non-sensitive feature and each sensitive attribute. |
| **Method** | Cramér's V (for categorical × categorical), point-biserial correlation (for numeric × binary categorical). Both are standard association measures appropriate for mixed-type datasets. |
| **Threshold** | Cramér's V ≥ 0.3 or absolute point-biserial r ≥ 0.3 triggers a "potential proxy" flag. Threshold is configurable in governance settings. |
| **Output** | Flagging only — not automatic removal. The UI highlights flagged features with an explanation: "This feature correlates with [sensitive attribute] at [strength]. It may act as a proxy for discrimination. Consider whether it is a valid predictor for the role." |
| **User action** | The human reviewer decides whether to retain, remove, or investigate the flagged feature. The decision is logged in the audit trail with justification. |
| **Limitations note** | Univariate correlation detection. Does not catch multivariate proxies (e.g., combinations of features that jointly predict a sensitive attribute). Multivariate proxy detection is scoped for post-MVP. |

**Post-MVP tabular interventions:**

| Intervention | What it does |
|---|---|
| **Representation balancing** | Resampling to correct demographic imbalance in training/evaluation data |
| **Threshold optimization** | Adjusts decision thresholds per group to equalize outcome rates |
| **Counterfactual sensitivity** | Tests how changing a sensitive attribute value changes the outcome for individual records |
| **Reject-option post-processing** | Gives favorable outcomes to borderline cases from disadvantaged groups |

**For LLM-assisted hiring workflows:**

| Intervention | What it does | MVP? |
|---|---|---|
| **Demographic perturbation testing** | Sends identical prompts with varied demographic markers; measures response disparities | ✓ MVP |
| **Job description bias scan** | Flags gendered/exclusionary language and suggests neutral alternatives | ✓ MVP |
| **Structured profile redaction** | Strips demographic signals (names, pronouns) from text-based candidate profiles before AI screening | Post-MVP |
| **Rubric-constrained evaluation** | Forces LLM to evaluate against explicit criteria rather than open-ended judgment | Post-MVP |
| **Decision normalization** | Standardizes LLM scoring outputs across demographic groups | Post-MVP |
| **Policy-based output checking** | Validates LLM outputs against organizational fairness policies before surfacing | Post-MVP |

**All interventions share these properties:**
- Before/after comparison dashboard showing metric changes
- Accuracy/quality impact displayed prominently
- Fairness-accuracy tradeoff visualization
- **No auto-apply.** Every intervention requires the user to:
  1. Review the before/after impact
  2. Select a strategy from available options
  3. Provide written justification for the choice
  4. Sign off with name, role, and timestamp

**Demo credibility note:** The remediation before/after story (e.g., DIR improving from 0.56 to 0.84) is demonstrated using synthetic placement data with planted disparities and the reweighting algorithm. This is a controlled simulation showing what reweighting achieves on known data — not a claim about real institutional outcomes. The demo clearly labels data provenance and states: "This analysis uses [synthetic/real/benchmark] data. Remediation effects are simulated on this dataset."

#### F8: Human Accountability Workflow
Three accountability touchpoints:
- **Analysis approval:** Before metrics are finalized, a named human confirms the analysis parameters
- **Tradeoff selection:** When choosing remediation, a named human selects the strategy and documents why
- **Report sign-off:** Before the audit report is generated, a named human reviews findings and signs off

Each touchpoint records: who (name + role), when (timestamp), what (the decision), and why (written justification).

#### F9: Applicant Recourse System

**Recourse Summary (applicant-facing):**
A simplified document that organizations can share with affected individuals:
- What automated tools were used in the decision process
- What categories of factors were considered (not individual scores)
- Aggregate fairness statistics for the decision cycle
- How to request a human review
- Contact information for the reviewing authority

This supports explanation and recourse readiness for high-risk employment decision contexts under the EU AI Act (Article 86, Annex III) and aligns with India's "people-first governance" sutra.

**Recourse Workflow Policy:**

| Element | Definition |
|---|---|
| **Who can file** | Any individual affected by a decision in a NyayaLens-audited pipeline, via the recourse portal |
| **Who adjudicates** | The organization's designated Recourse Reviewer — a named role assigned in Governance settings. Must be different from the analyst who ran the audit. |
| **What the reviewer sees** | The anonymized applicant's profile (via org's own mapping), the audit findings for the relevant cycle, the mitigation decisions made, and the sign-off chain |
| **Resolution states** | `pending` → `in_review` → `resolved_upheld` (original decision stands with documented reasoning) or `resolved_overturned` (decision reversed or applicant re-evaluated) or `resolved_referred` (escalated to external authority) |
| **Can a review overturn a decision?** | Yes. The reviewer can recommend reversal, re-evaluation, or escalation. NyayaLens documents the recommendation; the organization implements it through their own HR process. |
| **Target SLA** | Configurable by organization. Default: acknowledgment within 5 business days, resolution within 15 business days. SLA is a policy setting, not a system enforcement. |
| **Documentation** | Every recourse request, review action, and resolution is logged in the immutable audit trail with timestamp, reviewer identity, and reasoning. |

#### F10: PDF Audit Report Generator
Generates a comprehensive, downloadable audit report with explicit separation of evidence types:

**Part A — Audit Findings (from real/public data):**
1. Executive summary (Gemini-generated, grounded in metrics)
2. Dataset overview with demographic breakdowns and data provenance label
3. Fairness metrics with explanations and metric availability notes
4. Bias heatmap (embedded) with subgroup-size warnings where applicable
5. Metric conflict analysis

**Part B — Probe Findings (from LLM-generated scenarios):**
6. LLM Bias Probe results with data provenance label ("LLM-generated test scenario")
7. Demographic perturbation analysis
8. Job description bias scan results

**Part C — Governance Record:**
9. Mitigation analysis with tradeoff documentation and before/after comparisons
10. Human accountability chain (who approved what, when, why)
11. Applicant recourse template
12. Regulatory alignment checklist
13. Methodology appendix with formulas, thresholds, and data processing notes

Audit Findings and Probe Findings are always in separate, clearly labeled sections. The report never intermixes real-data findings with LLM-generated scenario results.

#### F11: LLM Bias Probe
Probes generative AI models for demographic bias in hiring contexts:
- **Job description analysis:** Tests whether AI-generated job descriptions contain gendered or exclusionary language
- **Resume screening probe:** Sends identical candidate profiles with varied demographic markers (names, pronouns) and measures scoring disparities
- **Response comparison view:** Side-by-side display of AI responses across demographic variations
- **Disparity quantification:** Statistical measurement of response differences

### 6.2 Hiring-First Core with Future Domain Extensibility

The core engine is domain-agnostic. The hiring-specific features are implemented as a **domain layer** on top of the general engine:

```
┌─────────────────────────────────────────────┐
│         DOMAIN LAYERS (pluggable)            │
│  ┌────────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Hiring    │ │ Lending  │ │ Admissions│  │
│  │  (v1.0)    │ │ (future) │ │ (future)  │  │
│  └────────────┘ └──────────┘ └───────────┘  │
├─────────────────────────────────────────────┤
│         CORE ENGINE (domain-agnostic)        │
│  Schema Detection │ Bias Engine │ Explain    │
│  Governance       │ Remediation │ Reporting  │
│  Recourse         │ Audit Trail │ LLM Probe  │
└─────────────────────────────────────────────┘
```

Each domain layer provides:
- Domain-specific Gemini prompts (e.g., hiring language vs. lending language)
- Domain-specific recourse templates
- Domain-specific regulatory checklists
- Domain-specific sample datasets
- Domain-specific explanation context

The core engine provides:
- Statistical metric computation
- Data ingestion and validation
- Gemini API integration
- Governance workflows
- Report generation
- User management
- Audit trail

This means the system can handle any tabular decision dataset with appropriate domain context. The hiring domain layer makes the hiring use case *better* through domain-specific prompts, templates, and regulatory context.

### 6.3 Dual Evidence Modes

NyayaLens operates in two distinct evidence modes. These are never conflated in the product, the documentation, or the demo.

#### Mode A: Audit Mode
Analyzes real, public, or organization-approved datasets for disparities and runs the full accountability workflow (detect → explain → govern → remediate → sign off → report).

Evidence produced: "Your placement data from 2023-2025 shows these disparity patterns."
Strength: Real institutional findings.
Limitation: Requires real data access, results reflect data quality.

#### Mode B: Probe Mode
Uses Gemini or Gemma 4 to generate synthetic scenarios — job descriptions, candidate profiles, screening rationales, name/pronoun variations — and then detects bias in the AI's own outputs.

Evidence produced: "When asked to evaluate identical candidates with different demographic markers, the AI model showed these response disparities."
Strength: Exposes AI system bias, privacy-safe, controllable.
Limitation: Measures model behavior, not institutional behavior. Results should not be presented as equivalent to real-world audit findings.

This separation is architecturally clean and intellectually honest. The demo uses both modes to tell a complete story: "Here's what your data shows (Audit), and here's what your AI tool does when we test it (Probe)."

**Metric Availability by Evidence Mode:**

Not all metrics are equally meaningful across all data types. NyayaLens makes this explicit:

| Metric | Audit Mode (full outcome data) | Audit Mode (outcome-only, sparse) | Probe Mode (LLM outputs) |
|---|---|---|---|
| **SPD** | ✓ Full support | ✓ Full support | ✓ On generated scores |
| **DIR** | ✓ Full support | ✓ Full support | ✓ On generated scores |
| **EOD** | ✓ Requires ground truth labels | ⚠ May lack ground truth — shown with caveat | ✗ Not applicable |
| **Consistency** | ✓ Requires numeric features | ⚠ Needs sufficient feature columns — shown with caveat | ✗ Not applicable |
| **Calibration** | ✓ Requires probability scores | ✗ Unavailable — requires probability scores; outcome-rate differences are captured by SPD/DIR | ✗ Not applicable |

When a metric cannot be computed meaningfully for the given data context, NyayaLens displays a clear indicator: "This metric requires [ground truth labels / numeric features / probability scores] which are not available in this dataset. Results are approximate." Metrics are never silently omitted — unavailability is always surfaced and explained.

### 6.4 Three-Tier Data Strategy

Given real-world data access constraints, NyayaLens implements a three-tier data strategy:

**Tier 1: Real, Privacy-Safe Anchor Data**
A small, manually collected, de-identified slice of real placement or hiring data. Stripped of direct identifiers, manually approved for use. This is the reality anchor — it proves the tool works on genuine data, even if the sample is small (200-500 records).

**Tier 2: Public Benchmark Datasets**
Established fairness research datasets (Adult Income, German Credit) used for method validation and baseline comparison. These demonstrate that NyayaLens metrics produce results consistent with published research. They are never presented as the team's own findings.

**Tier 3: Synthetic and LLM-Generated Challenge Sets**
The primary demo and stress-testing layer:
- Synthetic campus hiring data with planted disparities for reliable demo behavior
- Gemini/Gemma 4-generated candidate pools that expose LLM bias patterns
- Controlled metric conflict scenarios for testing the governance workflow
- Recourse scenario simulations

**Critical caveat (always displayed in product):** When analyzing synthetic or LLM-generated data, NyayaLens clearly labels the data provenance: "This analysis is based on [real/public benchmark/synthetic/LLM-generated] data. Findings from synthetic data reflect model behavior and testing scenarios, not institutional outcomes."

### 6.5 Model Backend Flexibility

NyayaLens supports two model backends for AI-assisted analysis:

**Gemini API (Primary — MVP):** Hosted inference for schema detection, explanations, and Probe Mode scenario generation. Production-ready, rate-limited, cloud-dependent.

**Gemma 4 (Optional — Strategic):** Google's latest open-weight models (released March 31, 2026) for privacy-preserving local deployments. Initially focused on Probe Mode (bias scenario generation and analysis) rather than core audit scoring. Enables organizations that cannot send data to cloud APIs to still use NyayaLens's AI capabilities.

The architecture abstracts the model backend behind a common interface, allowing users to select Gemini or Gemma 4 based on their privacy requirements, compute availability, and use case. This flexibility is a production-grade design pattern, not a demo gimmick.

---

## 7. System Architecture

NyayaLens is designed as a **service-oriented modular monolith** — a modular monolith with asynchronous workers and future-ready service extraction. We maintain strong internal service boundaries in code (each module has its own interface, data contract, and error handling), while deploying as a single Cloud Run container for simplicity. Cloud Functions handle asynchronous workloads (PDF generation, large-batch analysis, LLM probing). As usage and workload diversity grow, high-compute components can be selectively extracted into independent services without architectural refactoring.

### 7.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                              │
│          Web-first Flutter client (MVP); mobile post-MVP        │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Upload   │ │Dashboard │ │ Govern   │ │ Recourse │          │
│  │ Wizard   │ │& Visuals │ │ Panel    │ │ Portal   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ LLM Bias │ │ Report   │ │ Settings │                       │
│  │ Probe    │ │ Viewer   │ │ & Auth   │                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTPS REST + WebSocket
                        │ (Firebase Auth JWT tokens)
┌───────────────────────┴─────────────────────────────────────────┐
│                    API GATEWAY LAYER                             │
│              Google Cloud Run (auto-scaling)                     │
│              FastAPI + Python 3.11 + Uvicorn                     │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Auth         │ │ Rate Limit   │ │ Request      │           │
│  │ Middleware   │ │ Middleware   │ │ Validation   │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
├─────────────────────────────────────────────────────────────────┤
│                    SERVICE LAYER                                │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Schema   │ │ Bias     │ │ Explain  │ │Remediate │          │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │          │
│  │          │ │          │ │          │ │          │          │
│  │ Gemini   │ │ NumPy    │ │ Gemini   │ │ Custom   │          │
│  │ API      │ │ Pandas   │ │ API      │ │ Python   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Govern   │ │ Recourse │ │ LLM Probe│ │ Report   │          │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │          │
│  │          │ │          │ │          │ │          │          │
│  │ RBAC     │ │ Template │ │ Gemini   │ │ PDF Gen  │          │
│  │ + Audit  │ │ Engine   │ │ API      │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                    DATA LAYER                                   │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ Firebase │ │ Cloud    │ │ Cloud    │                       │
│  │ Auth     │ │ Firestore│ │ Storage  │                       │
│  │          │ │          │ │          │                       │
│  │ Google   │ │ Metadata │ │ Dataset  │                       │
│  │ Sign-In  │ │ Results  │ │ Files    │                       │
│  │ Email/PW │ │ Audit    │ │ Reports  │                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
├─────────────────────────────────────────────────────────────────┤
│                    ASYNC PROCESSING LAYER                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │            Google Cloud Functions                 │          │
│  │                                                   │          │
│  │  MVP:                                             │          │
│  │  • PDF report generation                          │          │
│  │  • Large dataset processing (>50MB)               │          │
│  │                                                   │          │
│  │  Post-MVP extensions:                             │          │
│  │  • Scheduled audit reminders                      │          │
│  │  • Email notifications                            │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Service-Level Architecture (Detailed)

#### 7.2.1 Schema Service

**Responsibility:** Understand uploaded datasets and identify relevant columns.

**Input:** Raw CSV/Excel file (first 1000 rows sampled for analysis).

**Process:**
1. Parse file, infer data types (numeric, categorical, datetime, text, boolean)
2. **PII Pre-Scrubber (runs BEFORE any data touches Gemini):**
   - Regex-based detection of email patterns, phone numbers, Aadhaar-like numbers, roll numbers
   - Name-column heuristic detection (high cardinality + string type + no repeats)
   - All detected PII columns are masked/hashed before LLM transmission
   - Only column headers, data types, value distribution summaries, category counts, and redacted sample values are sent to Gemini
   - Raw names, emails, phone numbers, free-text remarks NEVER reach the LLM
3. Generate column statistics (unique values, distribution, null percentage)
4. Send sanitized column metadata to Gemini API with structured output prompt
4. Gemini returns JSON: `{ sensitive_attributes: [...], outcome_column: "...", feature_columns: [...], identifier_columns: [...] }`
5. Apply confidence scoring based on Gemini's structured output
6. Return schema analysis to client for user confirmation

**Gemini Prompt Design:**
```
System: You are a data schema analyst specializing in fairness-sensitive datasets.
Given column names and sample values, identify:
1. Which columns represent protected/sensitive attributes
   (gender, sex, age, race, ethnicity, caste, religion, disability, 
   marital status, nationality, sexual orientation)
2. Which column is the decision/outcome column
   (hired, selected, approved, score, result, outcome, decision)
3. Which columns are predictive features
4. Which columns are identifiers (name, ID, email)

Respond ONLY in JSON. Include confidence scores (0-1) for each classification.
Consider Indian naming conventions: "Category" often means caste reservation,
"Community" may indicate religion, "Quota" may indicate reservation status.
```

**Error handling:**
- If Gemini confidence < 0.6 for any column, flag for mandatory user review
- If no outcome column detected, prompt user to select one
- If no sensitive attributes detected, warn user and allow manual specification

#### 7.2.2 Bias Service

**Responsibility:** Compute fairness metrics across all sensitive attributes.

**Implementation:** Custom Python engine using NumPy and Pandas. NOT wrapping AIF360 or Fairlearn — built from scratch for three reasons:
1. No dependency conflicts
2. Full control over edge case handling
3. 5 metrics instead of 70 = simpler, faster, more maintainable

**Metric implementations (pseudocode):**

```python
def statistical_parity_difference(y_pred, sensitive_attr):
    """Difference in positive outcome rates between groups."""
    groups = sensitive_attr.unique()
    rates = {}
    for group in groups:
        mask = sensitive_attr == group
        rates[group] = y_pred[mask].mean()
    
    privileged = max(rates, key=rates.get)
    unprivileged = min(rates, key=rates.get)
    spd = rates[unprivileged] - rates[privileged]
    return spd, rates, privileged, unprivileged

def disparate_impact_ratio(y_pred, sensitive_attr):
    """Ratio of positive outcome rates (80% rule)."""
    groups = sensitive_attr.unique()
    rates = {}
    for group in groups:
        mask = sensitive_attr == group
        rates[group] = y_pred[mask].mean()
    
    privileged = max(rates, key=rates.get)
    unprivileged = min(rates, key=rates.get)
    
    if rates[privileged] == 0:
        return float('inf'), rates, privileged, unprivileged
    
    dir_ratio = rates[unprivileged] / rates[privileged]
    return dir_ratio, rates, privileged, unprivileged

def equal_opportunity_difference(y_true, y_pred, sensitive_attr):
    """Difference in true positive rates."""
    groups = sensitive_attr.unique()
    tpr = {}
    for group in groups:
        mask = sensitive_attr == group
        positives = y_true[mask] == 1
        if positives.sum() == 0:
            tpr[group] = None
            continue
        tpr[group] = y_pred[mask][positives].mean()
    
    valid_tpr = {k: v for k, v in tpr.items() if v is not None}
    privileged = max(valid_tpr, key=valid_tpr.get)
    unprivileged = min(valid_tpr, key=valid_tpr.get)
    eod = valid_tpr[unprivileged] - valid_tpr[privileged]
    return eod, tpr, privileged, unprivileged

def consistency_score(X_features, y_pred, n_neighbors=5):
    """How similarly similar individuals are treated."""
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=n_neighbors)
    nn.fit(X_features)
    _, indices = nn.kneighbors(X_features)
    
    consistency = 1 - np.abs(
        y_pred.values - 
        np.array([y_pred.iloc[idx].mean() for idx in indices])
    ).mean()
    return consistency

def calibration_difference(y_true, y_prob, sensitive_attr, n_bins=10):
    """Predicted probability accuracy across groups."""
    groups = sensitive_attr.unique()
    calibration = {}
    for group in groups:
        mask = sensitive_attr == group
        if mask.sum() < n_bins:
            calibration[group] = None
            continue
        bins = np.linspace(0, 1, n_bins + 1)
        bin_means = []
        for i in range(n_bins):
            bin_mask = (y_prob[mask] >= bins[i]) & (y_prob[mask] < bins[i+1])
            if bin_mask.sum() > 0:
                bin_means.append(abs(
                    y_true[mask][bin_mask].mean() - 
                    y_prob[mask][bin_mask].mean()
                ))
        calibration[group] = np.mean(bin_means) if bin_means else None
    
    valid = {k: v for k, v in calibration.items() if v is not None}
    if len(valid) < 2:
        return None, calibration
    return max(valid.values()) - min(valid.values()), calibration
```

**Edge case handling:**
- Groups with < 30 samples: flagged as "insufficient sample size", metric reported with warning
- Missing values in sensitive attributes: treated as separate group "Unknown" + warning
- Binary vs. multi-class outcomes: SPD/DIR computed pairwise for multi-class
- Continuous outcomes: binned using domain-appropriate thresholds

#### 7.2.3 Explain Service

**Responsibility:** Generate grounded, plain-language explanations for all metric results.

**Design principle:** Metrics-first, explanation-second. Gemini translates pre-computed numbers into language. It never generates numbers.

**Prompt template:**
```
System: You are an AI fairness analyst writing for a non-technical 
HR compliance officer. You explain statistical findings in clear, 
actionable language. You NEVER declare a system "fair" or "unfair." 
You present evidence and ask the reader to investigate.

IMPORTANT: Every number in your explanation must come from the 
provided data. Do not generate, estimate, or round any numbers. 
Use the exact values provided.

Your explanation must include:
1. A one-sentence summary of the finding
2. What this metric measures and why it matters
3. How the result compares to common legal/regulatory thresholds
4. Possible root causes to investigate (not conclusions)
5. A clear statement that this is investigative guidance, not judgment

Context:
- Domain: {domain}
- Metric: {metric_name}
- Value: {metric_value}
- Threshold: {threshold}
- Privileged group: {privileged_group}
- Unprivileged group: {unprivileged_group}
- Group rates: {group_rates}
- Sample sizes: {sample_sizes}
```

**Hallucination prevention:**
1. All numeric values are injected into the prompt from the Bias Service output
2. Gemini's response is validated against the injected values using regex matching
3. If any number in the response differs from the injected values, the explanation is regenerated
4. Every explanation ends with: "This analysis is interpretive guidance to support human decision-making. It is not legal, ethical, or compliance advice."
5. Temperature set to 0.2 for factual consistency

#### 7.2.4 Govern Service

**Responsibility:** Manage organizational policies, role assignments, and accountability workflows.

**Components:**

**Policy Configuration:**
- Risk tolerance thresholds (e.g., DIR warning at 0.85, critical at 0.80)
- Approval requirements (who must sign off at each stage)
- Documentation requirements (what justification is needed)
- Recourse policy (what information is shared with affected individuals)

**Role-Based Access Control:**
- **Admin:** Full access, policy configuration, user management
- **Analyst:** Upload data, run analysis, generate reports
- **Reviewer:** Review findings, sign off on tradeoffs
- **Viewer:** Read-only access to reports and dashboards

**Audit Trail:**
Every action is logged to Firestore with:
```json
{
  "action": "tradeoff_selection",
  "user_id": "uid_123",
  "user_name": "Priya Sharma",
  "user_role": "HR Compliance Officer",
  "timestamp": "2026-04-21T14:30:00Z",
  "details": {
    "metric": "disparate_impact_ratio",
    "original_value": 0.56,
    "remediated_value": 0.84,
    "accuracy_impact": -0.018,
    "strategy": "reweighting",
    "justification": "Accepted 1.8% accuracy reduction to bring DIR within 80% threshold for gender attribute."
  }
}
```

#### 7.2.5 Recourse Service

**Responsibility:** Generate applicant-facing transparency summaries.

**Output:** A structured document containing:
- What automated system was used in the decision process
- What categories of factors were considered (not individual scores)
- Aggregate fairness statistics for the decision cycle
- How to request a human review of the decision
- Contact information for the reviewing authority
- Relevant regulatory references (EU AI Act Article 86, India AI Sutra 2)

**What is NOT included (privacy boundary):**
- Individual applicant scores or rankings
- Proprietary model details or weights
- Other applicants' information
- Internal deliberation notes

#### 7.2.6 LLM Probe Service

**Responsibility:** Test generative AI models for demographic bias in hiring contexts.

**Two probe types:**

**Type 1: Job Description Bias Probe**
- User provides a job title or role description
- NyayaLens sends parallel requests to Gemini:
  - "Write a job description for a software engineer"
  - "Write a job description for a software engineer (ensure gender-neutral language)"
- Analyzes the default output for gendered language patterns using a curated word list + Gemini analysis
- Reports: gendered words found, inclusivity score, recommended alternatives

**Type 2: Resume Screening Bias Probe**
- User provides evaluation criteria for a role
- NyayaLens generates identical candidate profiles with varied demographic markers:
  - Same qualifications, experience, education
  - Different names signaling different demographics (culturally appropriate name sets)
- Sends each profile to Gemini with the same evaluation prompt
- Measures: rating differences, language differences, recommendation differences
- Presents side-by-side comparison with statistical significance

**Critical design note:** The probe tests Gemini itself. This is intentional — it demonstrates that NyayaLens provides value regardless of which AI system is being audited, including the model powering NyayaLens's own intelligence layer. This recursive capability is architecturally meaningful, not decorative.

#### 7.2.7 Report Service

**Responsibility:** Generate comprehensive PDF audit reports.

**Implementation:** Cloud Function triggered asynchronously. Uses ReportLab (Python) for PDF generation.

**Report structure (aligned with F10 product specification):**

Cover page: NyayaLens branding, organization name, audit date, data provenance label.

**Part A — Audit Findings (from real/public data):**
1. Executive summary (Gemini-generated, grounded in metrics)
2. Dataset overview: rows, columns, demographic distributions, data provenance
3. Schema analysis: detected attributes and user confirmations
4. Fairness metrics table with visual indicators and subgroup-size warnings
5. Bias heatmap (embedded as image)
6. Detailed per-metric analysis with explanations
7. Metric conflict analysis (if applicable)

**Part B — Probe Findings (from LLM-generated scenarios):**
8. LLM Bias Probe results with data provenance label
9. Demographic perturbation analysis
10. Job description bias scan results (if run)

**Part C — Governance Record:**
11. Mitigation analysis with before/after comparisons and tradeoff documentation
12. Human accountability chain: who approved, when, what decision, why
13. Applicant recourse template
14. Regulatory alignment checklist (EU AI Act, India AI Sutras, NIST AI RMF)
15. Methodology appendix: formulas, reference thresholds, data processing notes
16. Digital signatures: analyst name, reviewer name, sign-off timestamps

Parts A and B are always clearly separated. If an audit did not include a Probe Mode run, Part B is omitted.

---

## 8. Data Architecture & Schema Design

### 8.1 Firestore Collections

```
nyayalens/
├── users/
│   └── {uid}/
│       ├── displayName: string
│       ├── email: string
│       ├── role: "admin" | "analyst" | "reviewer" | "viewer"
│       ├── organizationId: string
│       └── createdAt: timestamp
│
├── organizations/
│   └── {orgId}/
│       ├── name: string
│       ├── policy: {
│       │   ├── dirWarningThreshold: number (default: 0.85)
│       │   ├── dirCriticalThreshold: number (default: 0.80)
│       │   ├── spdThreshold: number (default: 0.10)
│       │   ├── requiredApprovers: string[]
│       │   └── recourseEnabled: boolean
│       │ }
│       └── createdAt: timestamp
│
├── audits/
│   └── {auditId}/
│       ├── organizationId: string
│       ├── createdBy: string (uid)
│       ├── status: "draft" | "analyzing" | "reviewed" | "signed_off" | "archived"
│       ├── datasetRef: string (Cloud Storage path)
│       ├── domain: "hiring" | "lending" | "admissions" | "general"
│       ├── schema: {
│       │   ├── sensitiveAttributes: [{ column: string, type: string, confidence: number }]
│       │   ├── outcomeColumn: { column: string, positiveValue: any }
│       │   ├── featureColumns: string[]
│       │   └── identifierColumns: string[]
│       │ }
│       ├── schemaConfirmedBy: string (uid)
│       ├── schemaConfirmedAt: timestamp
│       ├── metrics: {
│       │   └── {attributeName}: {
│       │       ├── spd: { value: number, groups: {}, privileged: string, unprivileged: string }
│       │       ├── dir: { value: number, groups: {}, privileged: string, unprivileged: string }
│       │       ├── eod: { value: number, tpr: {}, privileged: string, unprivileged: string }
│       │       ├── consistency: { value: number }
│       │       └── calibration: { value: number, perGroup: {} }
│       │   }
│       │ }
│       ├── explanations: {
│       │   └── {attributeName}: {
│       │       └── {metricName}: { text: string, generatedAt: timestamp }
│       │   }
│       │ }
│       ├── conflicts: [{ metric1: string, metric2: string, description: string }]
│       ├── remediation: {
│       │   ├── strategy: string
│       │   ├── beforeMetrics: {}
│       │   ├── afterMetrics: {}
│       │   ├── accuracyImpact: number
│       │   ├── selectedBy: string (uid)
│       │   ├── selectedAt: timestamp
│       │   └── justification: string
│       │ }
│       ├── signOff: {
│       │   ├── reviewerUid: string
│       │   ├── reviewerName: string
│       │   ├── reviewerRole: string
│       │   ├── signedAt: timestamp
│       │   └── notes: string
│       │ }
│       ├── reportRef: string (Cloud Storage path to PDF)
│       ├── recourseTemplateRef: string
│       ├── createdAt: timestamp
│       └── updatedAt: timestamp
│
├── audit_trail/
│   └── {trailId}/
│       ├── auditId: string
│       ├── action: string
│       ├── userId: string
│       ├── userName: string
│       ├── userRole: string
│       ├── timestamp: timestamp
│       ├── details: map
│       └── ipAddress: string
│
├── llm_probes/
│   └── {probeId}/
│       ├── auditId: string (optional, can be standalone)
│       ├── probeType: "job_description" | "resume_screening"
│       ├── config: {
│       │   ├── role: string
│       │   ├── criteria: string
│       │   └── demographicVariations: [{ name: string, markers: {} }]
│       │ }
│       ├── results: {
│       │   └── {variationName}: {
│       │       ├── response: string
│       │       ├── score: number (if applicable)
│       │       └── flaggedPatterns: string[]
│       │   }
│       │ }
│       ├── disparityAnalysis: {
│       │   ├── maxScoreDifference: number
│       │   ├── sentimentVariance: number
│       │   └── flaggedBiases: string[]
│       │ }
│       ├── createdBy: string
│       └── createdAt: timestamp
│
└── recourse_requests/
    └── {requestId}/
        ├── auditId: string
        ├── applicantIdentifier: string (anonymized)
        ├── requestType: "human_review" | "explanation" | "appeal"
        ├── status: "pending" | "in_review" | "resolved_upheld" | "resolved_overturned" | "resolved_referred"
        ├── assignedTo: string (uid)
        ├── reviewerNotes: string
        ├── createdAt: timestamp
        └── resolvedAt: timestamp
```

### 8.2 Cloud Storage Structure

```
nyayalens-bucket/
├── datasets/
│   └── {orgId}/
│       └── {auditId}/
│           ├── raw_upload.csv
│           └── processed_data.parquet
│
├── reports/
│   └── {orgId}/
│       └── {auditId}/
│           ├── audit_report.pdf
│           └── recourse_summary.pdf
│
└── exports/
    └── {orgId}/
        └── {auditId}/
            ├── heatmap.png
            └── metrics_export.json
```

---

## 9. API Design & Contracts

### 9.1 API Overview

Base URL: `https://nyayalens-api-{hash}.run.app/api/v1`
Authentication: Firebase Auth JWT Bearer tokens
Content-Type: application/json (except file uploads: multipart/form-data)

### 9.2 Endpoints

#### Dataset & Schema

```
POST   /datasets/upload
       Body: multipart/form-data { file, domain }
       Response: { datasetId, preview: { columns, sampleRows, rowCount } }

POST   /datasets/{datasetId}/detect-schema
       Body: { sampleSize?: number }
       Response: { schema: { sensitiveAttributes, outcomeColumn, features, identifiers } }

PUT    /datasets/{datasetId}/confirm-schema
       Body: { schema, confirmedBy }
       Response: { confirmed: true }
```

#### Bias Analysis

```
POST   /audits/{auditId}/analyze
       Body: { metrics: ["spd", "dir", "eod", "consistency", "calibration"] }
       Response: { jobId }  // async processing

GET    /audits/{auditId}/results
       Response: { status, metrics, heatmapData, conflicts }

POST   /audits/{auditId}/explain
       Body: { attribute, metric }
       Response: { explanation: { summary, details, rootCauses, considerations, disclaimer } }
```

#### Remediation

```
POST   /audits/{auditId}/remediate
       Body: { strategy: "reweighting", targetMetric: "dir", targetValue: 0.80 }
       Response: { beforeMetrics, afterMetrics, accuracyImpact, tradeoffAnalysis }

POST   /audits/{auditId}/remediate/approve
       Body: { strategy, justification, approverName, approverRole }
       Response: { approved: true, auditTrailId }
```

#### Governance

```
POST   /audits/{auditId}/sign-off
       Body: { reviewerName, reviewerRole, notes }
       Response: { signedOff: true, timestamp }

GET    /audits/{auditId}/audit-trail
       Response: { events: [...] }
```

#### Recourse

```
POST   /audits/{auditId}/recourse/generate
       Body: { language: "en" | "hi" }
       Response: { recourseDocument: { ... } }

POST   /recourse-requests
       Body: { auditId, applicantIdentifier, requestType }
       Response: { requestId, status: "pending" }
```

#### LLM Probe

```
POST   /llm-probes
       Body: { probeType, config: { role, criteria, variations } }
       Response: { probeId, status: "processing" }

GET    /llm-probes/{probeId}/results
       Response: { results, disparityAnalysis }
```

#### Reports

```
POST   /audits/{auditId}/report/generate
       Response: { jobId }  // async via Cloud Function

GET    /audits/{auditId}/report/status
       Response: { status: "generating" | "ready", downloadUrl? }
```

---

## 10. Process Flow Diagrams

### 10.1 Primary Flow: Complete Audit Lifecycle

```
[User uploads CSV/Excel]
        │
        ▼
[Schema Service: Gemini analyzes columns]
        │
        ▼
[User confirms/corrects schema detections]
        │
        ▼
[Bias Engine: Computes 5 metrics × N attributes]
        │
        ▼
[Explain Service: Gemini generates grounded explanations]
        │
        ├──── [No disparities found] ──── [Generate clean report] ──── [Sign off]
        │
        ▼
[Dashboard: Bias heatmap + metric cards + explanations]
        │
        ├──── [Metric conflicts detected]
        │           │
        │           ▼
        │     [Conflict surfacing: explain both sides]
        │           │
        │           ▼
        │     [User chooses which metric to prioritize]
        │           │
        │           ▼
        │     [Record choice + justification]
        │
        ▼
[Remediation options presented with tradeoff analysis]
        │
        ▼
[User selects strategy + provides justification]
        │
        ▼
[Before/after comparison dashboard]
        │
        ▼
[Human sign-off: name, role, timestamp, notes]
        │
        ├──── [Generate applicant recourse summary]
        │
        ▼
[PDF audit report generated with full accountability chain]
        │
        ▼
[Report stored in Cloud Storage, accessible via dashboard]
```

### 10.2 LLM Bias Probe Flow

```
[User selects probe type: Job Description OR Resume Screening]
        │
        ├──── [Job Description Probe]
        │           │
        │           ▼
        │     [User enters role title + context]
        │           │
        │           ▼
        │     [Gemini generates default job description]
        │           │
        │           ▼
        │     [Language analyzer scans for gendered/exclusionary terms]
        │           │
        │           ▼
        │     [Results: flagged terms, inclusivity score, alternatives]
        │
        ├──── [Resume Screening Probe]
                    │
                    ▼
              [User enters evaluation criteria]
                    │
                    ▼
              [System generates N identical profiles with demographic variations]
                    │
                    ▼
              [Each profile sent to Gemini with same evaluation prompt]
                    │
                    ▼
              [Responses collected and analyzed]
                    │
                    ▼
              [Side-by-side comparison with disparity metrics]
                    │
                    ▼
              [Statistical significance testing on score differences]
```

### 10.3 Applicant Recourse Flow

```
[Organization completes audit + sign-off]
        │
        ▼
[Recourse summary generated for the audit cycle]
        │
        ▼
[Organization shares summary with affected applicants]
        │
        ▼
[Applicant reviews factors considered]
        │
        ├──── [Satisfied] ──── [No action needed]
        │
        ▼
[Applicant requests human review via recourse portal]
        │
        ▼
[Request logged in NyayaLens, assigned to designated reviewer]
        │
        ▼
[Reviewer conducts human review of the specific case]
        │
        ▼
[Resolution documented in audit trail]
        │
        ▼
[Applicant notified of outcome]
```

---

## 11. Use Case Diagrams

### 11.1 Actor Definitions

| Actor | Description | Key Goals |
|---|---|---|
| **HR Analyst** | Uploads data, runs analysis, interprets results | Understand where bias exists in hiring pipeline |
| **HR Compliance Officer** | Reviews findings, approves tradeoffs, signs off | Ensure accountability documentation is complete |
| **System Admin** | Configures policy, manages users, sets thresholds | Establish organizational fairness governance |
| **Affected Applicant** | Receives recourse summary, may request review | Understand what factors influenced their outcome |
| **Gemini API** | Auto-detects schema, generates explanations, probes LLMs | Provide intelligence layer (external actor) |

### 11.2 Use Case Table

| UC ID | Use Case | Primary Actor | Description |
|---|---|---|---|
| UC-01 | Upload Dataset | HR Analyst | Upload CSV/Excel file with hiring/decision data |
| UC-02 | Confirm Schema | HR Analyst | Review and confirm Gemini's attribute detections |
| UC-03 | Run Bias Analysis | HR Analyst | Execute fairness metrics across all attributes |
| UC-04 | View Dashboard | HR Analyst | Explore bias heatmap, metric cards, distributions |
| UC-05 | Read Explanations | HR Analyst | Read Gemini-generated plain-English explanations |
| UC-06 | Resolve Conflicts | HR Compliance Officer | Choose between conflicting metrics, document rationale |
| UC-07 | Select Remediation | HR Compliance Officer | Choose mitigation strategy, document tradeoff |
| UC-08 | Sign Off Report | HR Compliance Officer | Review and sign off on final audit findings |
| UC-09 | Generate Report | HR Analyst | Create downloadable PDF audit report |
| UC-10 | Configure Policy | System Admin | Set thresholds, roles, approval requirements |
| UC-11 | Run LLM Probe | HR Analyst | Test job descriptions or screening for bias |
| UC-12 | Generate Recourse | HR Compliance Officer | Create applicant-facing transparency summary |
| UC-13 | Request Review | Affected Applicant | Submit a request for human review of decision |
| UC-14 | Manage Users | System Admin | Add/remove users, assign roles |
| UC-15 | View Audit Trail | HR Compliance Officer | Review complete history of actions and decisions |

---

## 12. Wireframe Specifications

### 12.1 Screen Inventory

| Screen | Purpose | Key Components |
|---|---|---|
| **S01: Landing / Auth** | Authentication entry | Google Sign-In button, email/password, NyayaLens branding |
| **S02: Home Dashboard** | Overview of all audits | Audit cards (status, date, key findings), "New Audit" CTA |
| **S03: Upload Wizard** | Guided data upload | Drag-drop zone, file preview, domain selector |
| **S04: Schema Review** | Confirm detected attributes | Column cards with Gemini classifications, edit controls |
| **S05: Analysis Dashboard** | Core bias results | Bias heatmap, metric cards, attribute tabs, explanation panels |
| **S06: Conflict Resolution** | Handle metric disagreements | Side-by-side metric comparison, tradeoff explanation, choice form |
| **S07: Remediation Panel** | Apply and compare mitigation | Before/after metrics, accuracy slider, justification form |
| **S08: Sign-Off Screen** | Human accountability | Summary of findings, reviewer info form, digital signature |
| **S09: Report Viewer** | View/download PDF | Embedded PDF viewer, download button, share options |
| **S10: LLM Probe** | Test generative AI bias | Probe configuration, side-by-side results, disparity chart |
| **S11: Recourse Portal** | Applicant-facing page | Factors summary, review request form, status tracker |
| **S12: Governance Settings** | Admin policy config | Threshold sliders, role management, approval workflows |
| **S13: Audit Trail** | Action history | Chronological event log with filters |

### 12.2 Key Screen Wireframe Descriptions

#### S03: Upload Wizard

```
┌──────────────────────────────────────────────┐
│  NyayaLens          [Profile] [Settings]     │
├──────────────────────────────────────────────┤
│                                              │
│  New Audit                          Step 1/3 │
│  ─────────────────────────────────────────── │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │                                        │  │
│  │     📄 Drag & drop your dataset here   │  │
│  │                                        │  │
│  │     CSV, XLSX up to 100MB              │  │
│  │                                        │  │
│  │     [Browse Files]                     │  │
│  │                                        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Domain: [Hiring ▾]                          │
│                                              │
│  Or try with sample data:                    │
│  [College Placement Data] [German Credit]    │
│                                              │
│                              [Next →]        │
└──────────────────────────────────────────────┘
```

#### S05: Analysis Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│  NyayaLens    [Audits] [LLM Probe] [Settings]   [Profile]   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Audit: College Placement 2023-25        Status: Analyzing   │
│  [Audit Mode] [Real Data]  ← data provenance badge           │
│  ──────────────────────────────────────────────────────────── │
│                                                              │
│  ┌─ Bias Heatmap ───────────────────────────────────────┐    │
│  │          │ SPD    │ DIR    │ EOD    │ Consist│ Calib  │    │
│  │  Gender  │ -0.34  │ 0.56 ❗│ -0.28  │  0.72  │  0.08  │    │
│  │  Branch  │ -0.12  │ 0.78 ⚠│ -0.09  │  0.88  │  0.03  │    │
│  │  Category│ -0.22  │ 0.64 ❗│ -0.18  │  0.79  │  0.06  │    │
│  │  ST*     │  n/a   │  n/a   │  n/a   │  n/a   │  n/a   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ❗ Critical    ⚠ Warning    ✓ Within threshold              │
│  * ST: n=28, below minimum sample size (30). Results omitted.│
│                                                              │
│  ┌─ Selected: Gender × DIR ─────────────────────────────┐    │
│  │                                                       │    │
│  │  Disparate Impact Ratio: 0.56                         │    │
│  │  ──────────────────────────────────────────────────    │    │
│  │  Groups: Male (n=412), Female (n=188)                 │    │
│  │                                                       │    │
│  │  "Women in this placement dataset are placed at       │    │
│  │   only 56% the rate of men with equivalent CGPAs.     │    │
│  │   This is well below the 80% reference threshold      │    │
│  │   commonly used in employment fairness analysis."     │    │
│  │                                                       │    │
│  │  Possible factors to investigate:                     │    │
│  │  • Branch distribution (women concentrated in         │    │
│  │    branches with fewer placement opportunities)       │    │
│  │  • Company preferences (some companies may have       │    │
│  │    historically preferred male candidates)            │    │
│  │                                                       │    │
│  │  ⓘ This is interpretive guidance, not legal advice.   │    │
│  │                                                       │    │
│  │  [View Distribution] [Run Remediation] [Sign Off]     │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Wireframe notes:**
- **Data provenance badge** (top-left below title): Always visible. Shows evidence mode (Audit/Probe) and data source type (Real Data/Public Benchmark/Synthetic/LLM-Generated). Color-coded: green for real, blue for benchmark, amber for synthetic.
- **Subgroup-size warnings:** When any group has fewer than 30 samples, the row shows "n/a" with a footnote explaining the minimum sample size requirement. Metrics are never silently computed on insufficient samples.

#### S08: Sign-Off Screen

```
┌──────────────────────────────────────────────────────────────┐
│  NyayaLens                                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Audit Sign-Off                                              │
│  ──────────────────────────────────────────────────────────── │
│                                                              │
│  Summary of Findings:                                        │
│  • 3 critical disparities detected (Gender, Category)        │
│  • 1 warning (Branch × DIR)                                  │
│  • Remediation applied: Reweighting                          │
│  • Accuracy impact: -1.8%                                    │
│  • DIR improved: 0.56 → 0.84                                 │
│                                                              │
│  ┌─ Accountability Record ──────────────────────────────┐    │
│  │                                                       │    │
│  │  Your Name:  [________________________]               │    │
│  │  Your Role:  [________________________]               │    │
│  │  Date:       April 21, 2026 (auto)                    │    │
│  │                                                       │    │
│  │  Notes / Justification:                               │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │                                                │   │    │
│  │  │                                                │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ☐ I confirm I have reviewed these findings and       │    │
│  │    accept responsibility for this tradeoff decision.  │    │
│  │                                                       │    │
│  │  [Sign Off & Generate Report]                         │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 13. Technology Stack & Justification

| Technology | Component | Rationale | Role |
|---|---|---|---|
| **Flutter** | Frontend (web-first MVP, mobile follow-on) | Web-first for competition delivery. Flutter's widget ecosystem supports the data-heavy UI patterns NyayaLens requires (heatmaps, interactive charts, form-heavy governance flows). Mobile deployment follows naturally from the same codebase post-MVP. | Core |
| **Firebase Auth** | Authentication | Google Sign-In + email/password with native Firestore security rule integration for org-scoped RBAC. | Core |
| **Cloud Firestore** | Metadata, results, audit trail | Real-time sync for dashboard updates. Structured queries for audit trail retrieval. Security rules enforce organization-scoped access. | Core |
| **Cloud Storage** | Dataset files, reports | Blob storage for uploaded CSVs and generated PDFs. Resumable uploads for large files. Signed URLs for time-limited secure downloads. | Core |
| **Cloud Run** | API backend | Auto-scaling containerized Python backend. Scales to zero when idle. Handles the compute-intensive metric calculations and Gemini API orchestration. | Core |
| **Gemini API** | Schema detection, explanations, LLM probing | Powers the intelligence layer: auto-schema detection from sanitized metadata, grounded metric explanations, and demographic perturbation probing. | Core |
| **Cloud Functions** | Async processing | PDF report generation and large dataset processing. Event-driven and auto-scaling. Scheduled reminders and email notifications are scoped as post-MVP extensions. | Core |
| **Gemma 4** *(Optional)* | Privacy-preserving local inference | Google's latest open-weight models (March 2026). Enables local analysis for data-sovereignty-sensitive organizations. Initially focused on Probe Mode scenario generation. | Strategic |

**Total: 7 core + 1 strategic Google technologies.** Gemma 4 adds privacy and latest-tech depth without delivery risk.

### Supporting Libraries (Non-Google)

| Library | Purpose | Why |
|---|---|---|
| **FastAPI** | Python web framework | Async support, automatic OpenAPI docs, Pydantic validation |
| **NumPy / Pandas** | Statistical computation | Industry standard for numerical computing. Lightweight. |
| **ReportLab** | PDF generation | Python-native PDF creation with full layout control |
| **fl_chart** | Flutter charts | Native Flutter charting library for heatmaps and metric visualizations |
| **scikit-learn** | k-NN for consistency metric | Only used for NearestNeighbors in consistency score calculation |

---

## 14. Security, Privacy & Compliance

### 14.1 Data Security

- **In transit:** All API communication over HTTPS (TLS 1.3). Cloud Run enforces HTTPS.
- **At rest:** Cloud Storage and Firestore encrypt all data at rest by default (AES-256).
- **Authentication:** Firebase Auth with JWT tokens. All API endpoints validate tokens.
- **Authorization:** Firestore security rules enforce role-based access. API middleware validates user roles.
- **File validation:** Server-side file type checking (magic bytes, not just extension). Max file size: 100MB. Sandboxed processing.

### 14.2 Privacy Architecture

NyayaLens implements a two-stage privacy pipeline:

**Stage A: Column-Level Structured PII Detection**
Before any data touches an LLM, the PII Pre-Scrubber runs:
- Exact-pattern detectors (email regex, phone patterns, Aadhaar/PAN formats)
- Statistical heuristics (high-cardinality string columns with >80% unique values → likely identifiers)
- Schema/column-name priors (columns matching "name", "email", "phone", "roll_no", etc.)
- All detected PII columns are masked or hashed before LLM transmission
- Only column headers, data types, distribution summaries, category counts, and redacted sample values reach the model

Design pattern inspired by Microsoft Presidio's recognizer architecture, adapted for Indian data formats (Aadhaar, PAN, roll numbers, reservation categories).

**Stage B: Free-Text and Cell-Level Inspection (Post-MVP)**
For datasets containing remarks, interview notes, or unstructured comments:
- Cell-level scanning for embedded names, contact information, institution IDs
- Redaction of PII within free-text fields before any LLM processing
- This stage is scoped for post-MVP but the architecture supports it from day one

**Privacy Modes:**

| Mode | What reaches the LLM | Best for |
|---|---|---|
| **Strict** | Only aggregate metadata — column names, types, distributions, counts. No row-level data at all. | Maximum privacy; slightly reduced schema detection accuracy |
| **Balanced** (default) | Sanitized column metadata + redacted sample values (PII columns hashed/masked) | Good schema detection with strong privacy |
| **Local** | All processing runs through Gemma 4 locally. No data leaves the organization's infrastructure. | Sovereignty-sensitive organizations, air-gapped environments |

**Privacy Logging:**
For every LLM call, the audit trail records:
- What columns were inspected
- What PII was detected and what masking was applied
- What exact metadata payload class was sent to the model
- Timestamp and model backend used (Gemini vs Gemma 4)

This turns privacy from a claim into an auditable mechanism.

**LLM Payload Contract:**
The following classes of data are permitted to reach Gemini/Gemma in each privacy mode:

| Data class | Strict mode | Balanced mode | Local mode |
|---|---|---|---|
| Column names | ✓ | ✓ | ✓ |
| Data types and null counts | ✓ | ✓ | ✓ |
| Value distributions / category counts | ✓ | ✓ | ✓ |
| Redacted sample values (PII masked) | ✗ | ✓ | ✓ |
| Aggregate metric results (for explanations) | ✓ | ✓ | ✓ |
| Raw individual rows | ✗ | ✗ | ✓ (local only) |
| Identifiers (names, emails, IDs) | ✗ | ✗ | ✗ (even locally) |

**Retention and Deletion Policy:**

| Artifact | Default retention | User-configurable? | Deletion behavior |
|---|---|---|---|
| Uploaded raw dataset | 90 days | ✓ (can set 0 = delete after analysis) | Hard delete from Cloud Storage |
| Processed/anonymized data | 12 months | ✓ | Hard delete |
| Metric results and explanations | 12 months | ✓ | Hard delete |
| Audit trail entries | 24 months | ✗ (minimum for compliance) | Append-only, archived after retention |
| PDF reports | 12 months | ✓ | Hard delete from Cloud Storage |
| Recourse request records | 24 months | ✗ (minimum for compliance) | Archived, not deleted |

**Re-Identification Boundary for Recourse:**
Applicant recourse summaries use anonymized identifiers (e.g., "Applicant #A7F3") that cannot be resolved back to real identities by the NyayaLens system itself. Re-identification is only possible by the deploying organization, which holds the mapping between anonymized IDs and real identities in their own HR systems. NyayaLens never stores or processes this mapping. When a recourse request is filed, the organization's designated reviewer is responsible for connecting the anonymized ID to the real applicant through their own records.

**Additional Privacy Controls:**
- **Data minimization:** Only the uploaded dataset and computed results are stored. Raw data can be deleted immediately after analysis.
- **Data provenance labeling:** Every analysis result is tagged with its data source type: real, public benchmark, synthetic, or LLM-generated. Displayed in UI and embedded in reports.
- **Anonymized recourse:** Applicant recourse summaries contain aggregate information only. No individual scores or rankings.
- **Synthetic data caveat:** When analyzing synthetic or LLM-generated data, a clear disclaimer is displayed: "Synthetic data findings reflect model behavior and testing scenarios, not real institutional outcomes."

### 14.3 Responsible AI

- **No automatic certification:** NyayaLens never declares "your system is fair" or "bias has been fixed." It says: "These are the disparities we detected, these are the mitigations we tested, these are the tradeoffs, and this is who approved the decision."
- **Grounded explanations:** All Gemini/Gemma outputs are validated against computed metrics. Numbers in explanations are injected from the engine, not generated by the LLM.
- **Disclaimer on every explanation:** "This is interpretive guidance to support human decision-making, not legal, ethical, or compliance advice."
- **Human-in-the-loop for all interventions:** No mitigation is applied silently. Every technical intervention requires human review, approval, and documented justification before deployment.
- **Audit trail immutability:** Once logged, audit trail entries cannot be modified or deleted (append-only).

---

## 15. Scalability & Performance Engineering

### 15.1 Performance Targets

| Operation | Target Latency | Strategy |
|---|---|---|
| File upload (50MB) | < 10s | Cloud Storage resumable upload |
| Schema detection | < 5s | Gemini API with structured output (1000-row sample) |
| Bias analysis (5 metrics, 100K rows) | < 15s | Vectorized NumPy operations, no loops |
| Explanation generation | < 3s | Gemini Flash model, low temperature |
| Remediation computation | < 10s | Vectorized reweighting |
| PDF report generation | < 30s | Async Cloud Function |

### 15.2 Scaling Strategy

- **Cloud Run auto-scaling:** Min instances: 0, Max instances: 10. Scales based on request concurrency.
- **Cloud Functions:** Auto-scaling, pay-per-invocation. No cold start management needed.
- **Firestore:** Auto-scales reads/writes. No capacity planning required.
- **Gemini API:** Rate limited at 60 RPM (free tier). Implement request queuing and caching for demo.

### 15.3 Caching Strategy

- Schema detection results cached in Firestore (re-detection not needed for same dataset)
- Explanation results cached per metric/attribute combination
- Heatmap rendered client-side from cached metric data
- PDF reports cached in Cloud Storage with signed URLs

---

## 16. Estimated Implementation Cost

### 16.1 Infrastructure Cost (Monthly, Production)

| Service | Free Tier | Estimated Usage | Monthly Cost |
|---|---|---|---|
| Cloud Run | 2M requests/month | ~50K requests | $0 (free tier) |
| Firestore | 50K reads, 20K writes/day | ~10K reads, 5K writes/day | $0 (free tier) |
| Cloud Storage | 5GB | ~2GB | $0 (free tier) |
| Cloud Functions | 2M invocations/month | ~5K invocations | $0 (free tier) |
| Gemini API | 60 RPM, 1M tokens/day | ~100K tokens/day | $0 (free tier) |
| Firebase Auth | 10K verifications/month | ~500 users | $0 (free tier) |

**Total infrastructure cost for MVP: $0/month** (within free tiers)

### 16.2 Development Cost (if this were a paid project)

| Role | Hours | Rate (₹) | Total |
|---|---|---|---|
| 4 developers × 4 weeks × 40 hrs | 640 hrs | ₹500/hr | ₹3,20,000 |
| Cloud credits (Google provides for competition) | — | — | $0 |
| Domain registration (nyayalens.dev) | — | — | ₹900/year |
| **Total estimated cost** | | | **₹3,20,900** (~$3,800 USD) |

### 16.3 Scaling Cost (Post-Competition, 1000 Users)

| Service | Usage | Monthly Cost |
|---|---|---|
| Cloud Run | ~500K requests | ~$15 |
| Firestore | ~100K reads, 50K writes/day | ~$10 |
| Cloud Storage | ~50GB | ~$1 |
| Cloud Functions | ~50K invocations | ~$2 |
| Gemini API | ~1M tokens/day | ~$5 |
| **Total** | | **~$33/month** |

---

## 17. Development Timeline & Sprint Plan

### Build Phases

The build follows three distinct phases. Each phase produces a testable, demoable artifact.

**Phase A — Minimal MVP (Weeks 1-2):** The smallest working version of NyayaLens. A user can upload a CSV, see Gemini detect the schema, confirm it, run 5 fairness metrics, see a bias heatmap with Gemini explanations, and view metric conflict surfacing. This is the internal test artifact — built first, tested with the team, iterated before expanding.

**Phase B — Competition MVP (Weeks 3-4):** The submission-ready product. Adds reweighting remediation with before/after comparison, proxy-feature detection, human sign-off workflow, LLM Bias Probe (demographic perturbation + JD scan), PDF audit report generation, applicant recourse summary, and demo polish. User testing with classmates happens during this phase.

**Phase C — Post-MVP (after competition):** Mobile deployment, additional mitigation strategies (threshold optimization, representation balancing), scheduled audit reminders, email notifications, enterprise tenancy hardening, Gemma 4 local mode, multi-language support.

### Week 1: Foundation (Days 1-7)

| Day | Dev 1 (Frontend) | Dev 2 (Backend/ML) | Dev 3 (AI/Integration) | Dev 4 (Full-Stack/Demo) |
|---|---|---|---|---|
| 1-2 | Flutter project setup, auth flow, navigation | FastAPI skeleton, Cloud Run deployment, Docker setup | Gemini API integration, prompt engineering for schema detection | Firebase project setup, Firestore schema, Cloud Storage config |
| 3-4 | Upload wizard UI (drag-drop, preview, domain selector) | CSV parser, data type inference, validation engine | Schema detection endpoint, confidence scoring | Auth middleware, API gateway setup, error handling |
| 5-7 | Schema review screen (column cards, edit controls) | Metric engine: SPD + DIR implementation with tests | Schema confirmation flow, Gemini prompt refinement | Integration testing, CI/CD pipeline setup |

**Week 1 deliverable:** User can upload CSV → Gemini detects schema → user confirms → 2 metrics computed.

### Week 2: Core Engine (Days 8-14)

| Day | Dev 1 (Frontend) | Dev 2 (Backend/ML) | Dev 3 (AI/Integration) | Dev 4 (Full-Stack/Demo) |
|---|---|---|---|---|
| 8-10 | Dashboard layout, bias heatmap component (fl_chart), metric cards | Metric engine: EOD + Consistency + Calibration with tests | Explanation engine: per-metric Gemini prompts, grounding validation | Firestore integration for audit results, real-time sync |
| 11-12 | Explanation panel UI, drill-down views | Edge case handling: small groups, missing values, multi-class | Conflict detection logic, Gemini conflict explanation prompts | Audit trail logging, governance service skeleton |
| 13-14 | Conflict resolution screen, tradeoff comparison view | Performance optimization: vectorized operations, benchmarks | End-to-end integration testing with sample datasets | Test with college placement dataset, document findings |

**Week 2 deliverable:** Full dashboard working — heatmap, all 5 metrics, Gemini explanations, conflict surfacing.

### Week 3: Accountability + Innovation (Days 15-21)

| Day | Dev 1 (Frontend) | Dev 2 (Backend/ML) | Dev 3 (AI/Integration) | Dev 4 (Full-Stack/Demo) |
|---|---|---|---|---|
| 15-17 | Remediation panel (before/after, accuracy slider, justification form) | Reweighting algorithm, before/after computation, tradeoff analysis | LLM Probe backend: prompt generation, response analysis | Sign-off workflow, accountability chain, recourse service |
| 18-19 | Sign-off screen, LLM Probe UI (config, side-by-side results) | PDF report generation (ReportLab) via Cloud Function | LLM Probe: demographic variation engine, disparity quantification | User testing with 3-5 classmates using college placement data |
| 20-21 | Recourse portal UI (applicant-facing), report viewer | Integration testing, edge cases, error recovery | Explanation refinement based on user testing feedback | Document user feedback (3+ specific points), begin demo script |

**Week 3 deliverable:** Full lifecycle working — upload through sign-off and report. LLM Probe functional. User testing complete.

### Week 4: Polish + Submission (Days 22-28)

| Day | Dev 1 (Frontend) | Dev 2 (Backend/ML) | Dev 3 (AI/Integration) | Dev 4 (Full-Stack/Demo) |
|---|---|---|---|---|
| 22-23 | UI polish: animations, transitions, responsive design, accessibility | Performance testing, load testing, security review | Prompt refinement, explanation quality review, edge case handling | Demo video script finalization, begin recording |
| 24-25 | Final bug fixes, mobile optimization | API documentation, error handling improvements | Gemini prompt caching, rate limit handling | Demo video recording + editing |
| 26-27 | Deployment verification, cross-browser testing | Docker optimization, Cloud Run config tuning | Final integration testing | Submission documentation, project deck |
| 28 | Final review and sign-off | Final review and sign-off | Final review and sign-off | **SUBMIT** |

**Week 4 deliverable:** Polished, tested, documented product + 2-minute demo video + project deck + GitHub repo.

---

## 18. Regulatory Alignment Matrix

| Requirement | EU AI Act | India AI Sutras | NIST AI RMF | NyayaLens Feature |
|---|---|---|---|---|
| Risk assessment | Article 9 | Safety sutra | GOVERN 1.1 | Automated metric computation + risk scoring |
| Bias testing | Article 10 | Fairness sutra | MEASURE 2.6 | 5 fairness metrics + intersectional analysis |
| Human oversight | Article 14 | Accountability sutra | GOVERN 1.3 | Human sign-off workflow |
| Transparency | Article 13 | Understandability sutra | MAP 3.5 | Gemini explanations + recourse summaries |
| Documentation | Article 11 | Trust sutra | GOVERN 1.4 | PDF audit reports + audit trail |
| Logging | Article 12 | Accountability sutra | MEASURE 2.5 | Immutable audit trail in Firestore |
| Right to explanation | Article 86 | People-first sutra | MANAGE 4.1 | Applicant recourse portal |
| Grievance redressal | GDPR Art 22 | People-first sutra | MANAGE 4.2 | Recourse request workflow |
| Continuous monitoring | Article 72 | Safety sutra | MANAGE 4.3 | Audit versioning + scheduled re-analysis |

---

## 19. Future Roadmap

### Phase 1: Post-Competition (Month 1-2)
- Open-source release (Apache 2.0)
- Community contribution guidelines
- Additional domain layers: lending, admissions
- Expanded metric set (10 metrics)
- Multi-language support (Hindi, Tamil, Bengali)

### Phase 2: Platform Growth (Month 3-6)
- API for CI/CD pipeline integration (GitHub Action for automated bias testing)
- Additional remediation strategies (threshold calibration, oversampling)
- Scheduled recurring audits with drift detection
- Webhook integrations (Slack, Teams notifications)
- Model upload capability (audit custom ML models, not just datasets)

### Phase 3: Enterprise Features (Month 7-12)
- Enterprise tenancy hardening (advanced isolation, org-level data segregation, admin delegation)
- Team collaboration workspace with shared audit reviews
- Custom metric definitions
- On-premise deployment option
- SOC 2 compliance
- Enterprise SSO (SAML/OIDC)

### Phase 4: Ecosystem (Year 2)
- NyayaLens Marketplace (community-contributed domain layers)
- Regulatory automation (auto-generate compliance documentation per jurisdiction)
- Real-time production monitoring (ML model drift + fairness drift)
- International expansion (GDPR, CCPA, Brazil LGPD alignment)
- Agentic workflows via Google ADK: Google's open-source Agents CLI (github.com/google/agents-cli) enables building agentic applications on Google Cloud. Future NyayaLens versions could leverage ADK for automated audit scheduling, multi-step remediation pipelines, and cross-system accountability workflows where an agent orchestrates the full Measure → Mitigate → Govern → Recourse cycle with human checkpoints.

---

## 20. Appendices

### Appendix A: Sample Datasets for Demo

**1. College Placement Data (Primary Demo)**

Concrete schema for a typical Indian engineering college placement dataset:

| Column | Type | Role | Sample Values | Notes |
|---|---|---|---|---|
| `Name` | String | Identifier (PII) | "Rahul Sharma", "Priya Patel" | Scrubbed before analysis |
| `Roll_No` | String | Identifier (PII) | "21CS001", "21EC042" | Scrubbed before analysis |
| `Email` | String | Identifier (PII) | "student@college.edu" | Scrubbed before analysis |
| `Gender` | Categorical | Sensitive Attribute | "Male", "Female" | Primary fairness axis |
| `Branch` | Categorical | Sensitive Attribute | "CSE", "ECE", "ME", "CE", "EE" | May correlate with outcomes |
| `Category` | Categorical | Sensitive Attribute | "General", "OBC", "SC", "ST" | Reservation category |
| `CGPA` | Numeric (float) | Feature | 6.2, 7.8, 9.1 | Scale: 0-10 |
| `Backlogs` | Numeric (int) | Feature | 0, 1, 3 | Active + cleared |
| `Internships` | Numeric (int) | Feature | 0, 1, 2, 3 | Count of completed internships |
| `Projects` | Numeric (int) | Feature | 1, 2, 4 | Academic/personal projects |
| `Placed` | Binary (0/1) | Outcome | 0 = Not placed, 1 = Placed | Decision column |
| `Company` | Categorical | Feature | "TCS", "Infosys", "Google" | Recruiting company (if placed) |
| `Package_LPA` | Numeric (float) | Feature | 0, 3.6, 8.5, 24.0 | Annual CTC in lakhs |

Expected findings on real Indian placement data: gender disparities (women placed at lower rates), category disparities (SC/ST groups underrepresented in high-package placements), branch concentration effects (CSE dominates placements).

**2. German Credit Dataset (UCI):** 1000 instances, 20 attributes. Standard benchmark for fairness testing. Protected attributes: age, sex, foreign worker status.

**3. Adult Income Dataset (UCI):** 48,842 instances. Predict income >$50K. Protected attributes: race, sex, age.

**4. Custom Synthetic Dataset:** Controlled bias patterns for demo reliability. Generated with known disparities and seeded metric conflicts for consistent demo experience. Data provenance always labeled as "Synthetic."

### Appendix B: Glossary

| Term | Definition |
|---|---|
| **Protected attribute** | A characteristic (gender, race, age, etc.) that should not influence automated decisions |
| **Privileged group** | The demographic group receiving the most favorable outcomes |
| **Unprivileged group** | The demographic group receiving the least favorable outcomes |
| **Disparate impact** | When a seemingly neutral policy disproportionately affects a protected group |
| **80% rule** | The EEOC guideline that selection rates for any group should be at least 80% of the rate for the group with the highest rate |
| **Equalized odds** | True positive rates and false positive rates should be equal across groups |
| **Reweighting** | Assigning different weights to data instances to equalize group representation |
| **Recourse** | The ability for an affected individual to challenge or appeal an automated decision |

### Appendix C: Open Source Licensing

NyayaLens will be released under the **Apache License 2.0**, which:
- Allows commercial use, modification, distribution, and patent use
- Requires preservation of copyright and license notices
- Does not require derivative works to be open-sourced
- Is compatible with Google's open-source ecosystem

---

*NyayaLens: The Eye of Justice*
*Aligned with India AI Governance Sutras | NIST AI RMF | EU AI Act*
*Built with Google Technologies for Solution Challenge 2026: Build with AI*

---

**Document prepared by:** Team Zenith
**Version:** 5.0 (Final)
**Date:** April 23, 2026
