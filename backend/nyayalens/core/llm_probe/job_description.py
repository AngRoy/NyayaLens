"""Job-description bias scan — design doc §6.3 F11 sub-feature.

Lexical scan with a curated list of masculine- and feminine-coded words
(Gaucher et al. 2011 lineage) plus age- and disability-related phrasing.
The scanner produces an inclusivity score and rewrite suggestions; an
optional Gemini follow-up can deepen the rewrite, but for MVP the lexical
pass alone powers the demo.

Imported by:
- `core/llm_probe/__init__.py` re-exports
- `api/probes.py:job-description` POST endpoint (forthcoming)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

GENDERED_TERMS: dict[str, list[str]] = {
    "masculine_coded": [
        "aggressive",
        "ambitious",
        "assertive",
        "competitive",
        "decisive",
        "dominant",
        "driven",
        "fearless",
        "leader",
        "rockstar",
        "ninja",
        "guru",
        "hacker",
        "headstrong",
        "independent",
        "individualistic",
        "self-reliant",
        "strong",
        "superior",
        "rigorous",
    ],
    "feminine_coded": [
        "collaborative",
        "committed",
        "compassionate",
        "considerate",
        "cooperative",
        "dependable",
        "empathic",
        "emotional",
        "honest",
        "kind",
        "loyal",
        "modest",
        "nurturing",
        "patient",
        "polite",
        "supportive",
        "sympathetic",
        "trustworthy",
        "understanding",
        "warm",
    ],
    "age_coded": [
        "young",
        "youthful",
        "energetic",
        "fresh graduate",
        "digital native",
        "recent graduate",
        "new graduate",
        "millennial",
    ],
    "ability_coded": [
        "able-bodied",
        "must be able to",
        "stand for long periods",
        "physically demanding",
    ],
}

REWRITE_HINTS: dict[str, str] = {
    "rockstar": "high-impact engineer",
    "ninja": "specialist",
    "guru": "expert",
    "aggressive": "proactive",
    "dominant": "well-recognised",
    "fearless": "willing to take initiative",
    "young": "early-career",
    "youthful": "early-career",
    "energetic": "motivated",
    "fresh graduate": "early-career",
    "digital native": "comfortable with modern tools",
    "able-bodied": "(consider whether physical ability is an essential function)",
    "must be able to": "ability to",
    "rigorous": "thorough",
}

# Soft cap on penalty so any 4+ flags ≈ 0.0 inclusivity score.
INCLUSIVITY_PENALTY_CAP: float = 4.0


@dataclass(frozen=True, slots=True)
class FlaggedPhrase:
    phrase: str
    category: str
    suggestion: str = ""


@dataclass(frozen=True, slots=True)
class JdScanResult:
    job_title: str
    inclusivity_score: float
    flagged_phrases: list[FlaggedPhrase]
    rewrite_suggestions: list[str] = field(default_factory=list)
    backend: str = "lexical-scan"
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _word_pattern(term: str) -> re.Pattern[str]:
    if " " in term:
        return re.compile(re.escape(term), re.IGNORECASE)
    return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)


def scan_job_description(
    job_title: str,
    job_description: str,
) -> JdScanResult:
    """Run the lexical bias scan and return a UI-ready result."""
    flagged: list[FlaggedPhrase] = []
    seen: set[tuple[str, str]] = set()
    for category, terms in GENDERED_TERMS.items():
        for term in terms:
            if _word_pattern(term).search(job_description):
                key = (term, category)
                if key in seen:
                    continue
                seen.add(key)
                flagged.append(
                    FlaggedPhrase(
                        phrase=term,
                        category=category,
                        suggestion=REWRITE_HINTS.get(term, ""),
                    )
                )

    penalty = float(len(flagged))
    inclusivity_score = max(0.0, 1.0 - min(penalty / INCLUSIVITY_PENALTY_CAP, 1.0))

    rewrite_suggestions: list[str] = []
    for f in flagged:
        if f.suggestion:
            rewrite_suggestions.append(f"Replace '{f.phrase}' with '{f.suggestion}'.")
        elif f.category == "feminine_coded":
            rewrite_suggestions.append(
                f"'{f.phrase}' is feminine-coded; pair it with action-oriented framing."
            )
    if not rewrite_suggestions and flagged:
        rewrite_suggestions.append(
            "Consider neutral, action-focused framing (e.g. 'leads cross-functional projects')."
        )

    return JdScanResult(
        job_title=job_title,
        inclusivity_score=inclusivity_score,
        flagged_phrases=flagged,
        rewrite_suggestions=rewrite_suggestions,
    )


__all__ = [
    "GENDERED_TERMS",
    "INCLUSIVITY_PENALTY_CAP",
    "REWRITE_HINTS",
    "FlaggedPhrase",
    "JdScanResult",
    "scan_job_description",
]
