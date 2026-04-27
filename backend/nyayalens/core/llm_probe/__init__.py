"""LLM Bias Probe — design doc §6.3 F11.

Two probe types:
- `job_description`: scan an org's JD for gendered/exclusionary language.
- `resume_screening`: send identical candidate profiles with varied
  demographic markers and quantify response disparity.
"""

from nyayalens.core.llm_probe.job_description import (
    GENDERED_TERMS,
    JdScanResult,
    scan_job_description,
)
from nyayalens.core.llm_probe.resume_screening import (
    PerturbationProbeResult,
    VariantResult,
    run_perturbation_probe,
)

__all__ = [
    "GENDERED_TERMS",
    "JdScanResult",
    "PerturbationProbeResult",
    "VariantResult",
    "run_perturbation_probe",
    "scan_job_description",
]
